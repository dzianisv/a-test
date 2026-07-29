"""Screen recording and GIF assembly for a-test Android harness."""
import contextlib
import subprocess
import threading
import time
import json
from pathlib import Path

from .evidence import EvidenceGateError, gate_video_evidence
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


def start_screen_recording(scenario_name: str):
    """Start ADB screen recording. Returns (thread, remote_path).

    Stop it with stop_screen_recording(thread, remote_path, local_path), which
    signals the on-device recorder via `pkill -2 screenrecord` and pulls the MP4.
    """
    remote_path = f"/sdcard/cua_{scenario_name}.mp4"

    def _record():
        try:
            subprocess.run(
                ["adb", "shell", f"screenrecord --time-limit 180 {remote_path}"],
                capture_output=True, timeout=200,
            )
        except Exception:
            pass

    thread = threading.Thread(target=_record, daemon=True)
    thread.start()
    time.sleep(1.0)
    return thread, remote_path


def stop_screen_recording(thread, remote_path: str, local_path: str) -> bool:
    """Stop recorder, pull video to local_path. Returns True on success."""
    subprocess.run(
        ["adb", "shell", "pkill", "-2", "screenrecord"],
        capture_output=True, timeout=10,
    )
    time.sleep(2.0)
    thread.join(timeout=5)
    result = subprocess.run(
        ["adb", "pull", remote_path, local_path],
        capture_output=True, timeout=30,
    )
    if result.returncode == 0 and Path(local_path).exists():
        print(f"  [recording] saved to {local_path}")
        return True
    print(f"  [recording] pull failed: {result.stderr.decode(errors='replace').strip()}")
    return False


# --- Segmented recording (no 180s cap, constant-framerate output) ----------
#
# `adb screenrecord` has two production-breaking properties:
#   1. A hard --time-limit cap of 180s: naive use silently truncates long
#      journeys.
#   2. Variable framerate -- frames are emitted only on screen change, so a
#      177s session can contain 67 frames; a 10x speedup then yields a 3.6s
#      slideshow that looks like a static picture.
#
# SegmentedRecorder records N back-to-back <180s segments while the scenario
# runs, pulls them, re-encodes each to constant framerate, concatenates them
# (re-encoding at the concat step -- `-c copy` through the concat demuxer
# produces non-monotonic DTS from screenrecord segments), and optionally
# applies a speedup producing a Shorts-ready file.

SEGMENT_LIMIT_SECONDS = 175  # < adb screenrecord's 180s hard cap


def reencode_cfr(input_path: str, output_path: str, fps: int = 30) -> bool:
    """Re-encode a variable-framerate screenrecord to constant framerate."""
    result = subprocess.run(
        ["ffmpeg", "-y", "-fflags", "+genpts", "-i", input_path,
         "-vsync", "cfr", "-r", str(fps),
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-an", output_path],
        capture_output=True, timeout=600,
    )
    if result.returncode != 0:
        print(f"  [recording] CFR re-encode failed for {input_path}: "
              f"{result.stderr.decode(errors='replace').strip()[-300:]}")
        return False
    return True


def concat_segments(segment_paths: list, output_path: str, fps: int = 30,
                    speedup: float = 1.0) -> bool:
    """Concat CFR segments into one MP4, optionally sped up (audio dropped).

    Re-encodes at the concat step instead of stream-copying: `-c copy` with
    the concat demuxer produces non-monotonic DTS from screenrecord segments.
    """
    segments = [Path(p) for p in segment_paths if Path(p).exists() and Path(p).stat().st_size > 0]
    if not segments:
        print("  [recording] no segments to concat")
        return False

    list_path = Path(output_path).with_suffix(".concat.txt")
    list_path.write_text("\n".join(f"file '{p.resolve()}'" for p in segments))

    vf = f"setpts=PTS/{speedup}" if speedup and speedup != 1.0 else "null"
    result = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-fflags", "+genpts",
         "-i", str(list_path),
         "-vf", vf, "-vsync", "cfr", "-r", str(fps),
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", "-an", output_path],
        capture_output=True, timeout=600,
    )
    list_path.unlink(missing_ok=True)
    if result.returncode != 0:
        print(f"  [recording] concat failed: "
              f"{result.stderr.decode(errors='replace').strip()[-300:]}")
        return False
    return Path(output_path).exists() and Path(output_path).stat().st_size > 0


class SegmentedRecorder:
    """Record back-to-back adb screenrecord segments with no total time cap.

    Usage:
        rec = SegmentedRecorder("journey", output_dir)
        rec.start()
        ...run the scenario...
        final = rec.stop_and_finalize(fps=30, speedup=10.0)  # path or None

    `size` / `bitrate` map to screenrecord's --size / --bit-rate. Recording a
    1080x2400 device at native resolution on a contended host starves the
    on-device encoder: a 112s session has been observed emitting 67 frames,
    which is an unusable slideshow after any speedup and trips the evidence
    gate. Downscaling the capture (e.g. size="720x1600") keeps the encoder
    ahead of the display and is the difference between a real recording and a
    static picture. Left as None, screenrecord's own defaults apply.
    """

    def __init__(self, scenario_name: str, output_dir: str,
                 segment_limit: int = SEGMENT_LIMIT_SECONDS,
                 size: str | None = None, bitrate: int | None = None):
        self.scenario_name = scenario_name
        self.output_dir = Path(output_dir)
        self.segment_limit = segment_limit
        self.size = size
        self.bitrate = bitrate
        self.remote_segments: list = []
        self._stop = threading.Event()
        self._thread = None

    def _screenrecord_cmd(self, remote: str) -> str:
        parts = ["screenrecord", f"--time-limit {self.segment_limit}"]
        if self.size:
            parts.append(f"--size {self.size}")
        if self.bitrate:
            parts.append(f"--bit-rate {self.bitrate}")
        parts.append(remote)
        return " ".join(parts)

    def _record_loop(self):
        index = 0
        while not self._stop.is_set():
            remote = f"/sdcard/cua_{self.scenario_name}_seg{index:03d}.mp4"
            self.remote_segments.append(remote)
            try:
                subprocess.run(
                    ["adb", "shell", self._screenrecord_cmd(remote)],
                    capture_output=True, timeout=self.segment_limit + 30,
                )
            except Exception:
                break
            index += 1

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        time.sleep(1.0)  # let screenrecord spin up before the scenario acts
        return self

    def stop_and_finalize(self, fps: int = 30, speedup: float = 1.0):
        """Stop recording, pull + CFR-re-encode + concat segments.

        Returns the path to <output_dir>/<name>.mp4 on success, else None.
        """
        self._stop.set()
        subprocess.run(["adb", "shell", "pkill", "-2", "screenrecord"],
                       capture_output=True, timeout=10)
        time.sleep(2.0)  # screenrecord needs a beat to finalize the moov atom
        if self._thread:
            self._thread.join(timeout=10)

        seg_dir = self.output_dir / "segments"
        seg_dir.mkdir(parents=True, exist_ok=True)
        cfr_segments = []
        for i, remote in enumerate(self.remote_segments):
            raw = seg_dir / f"seg{i:03d}-raw.mp4"
            result = subprocess.run(["adb", "pull", remote, str(raw)],
                                    capture_output=True, timeout=120)
            if result.returncode != 0 or not raw.exists() or raw.stat().st_size == 0:
                continue
            subprocess.run(["adb", "shell", "rm", "-f", remote],
                           capture_output=True, timeout=10)
            cfr = seg_dir / f"seg{i:03d}-cfr.mp4"
            if reencode_cfr(str(raw), str(cfr), fps=fps):
                cfr_segments.append(str(cfr))

        if not cfr_segments:
            print("  [recording] no usable segments pulled")
            return None

        final = self.output_dir / f"{self.scenario_name}.mp4"
        if concat_segments(cfr_segments, str(final), fps=fps, speedup=speedup):
            print(f"  [recording] saved to {final} ({len(cfr_segments)} segment(s))")
            return str(final)
        return None


@contextlib.contextmanager
def record_verified_journey(scenario_name: str, output_dir: str,
                            fps: int = 30, speedup: float = 1.0,
                            frames: int = 6, min_distinct: int = 4,
                            size: str | None = None,
                            bitrate: int | None = None,
                            blank_mean: float | None = None):
    """Record a journey, then gate the video on real visual evidence.

    Yields a dict the scenario can inspect afterwards:
        video:   path to <output_dir>/<name>.mp4 (constant framerate, sped up)
        report:  evidence report dict (also written to <output_dir>/report.json)

    Raises EvidenceGateError if the recording fails the evidence gate
    (frame-starved, <min_distinct distinct screens, or blank frames), so an
    upload step placed after this block can never ship a static video.

        with record_verified_journey("signup", out, speedup=10) as journey:
            run_scenario()
        upload(journey["video"])  # only reached when evidence passed
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    recorder = SegmentedRecorder(scenario_name, output_dir,
                                 size=size, bitrate=bitrate).start()
    journey = {"video": None, "report": None}
    try:
        yield journey
    finally:
        journey["video"] = recorder.stop_and_finalize(fps=fps, speedup=speedup)

    report_path = str(Path(output_dir) / "report.json")
    if journey["video"] is None:
        raise EvidenceGateError({"verdict": "fail",
                                 "failures": ["recording produced no video"]})
    gate_kwargs = {"frames": frames, "min_distinct": min_distinct,
                   "report_path": report_path}
    if blank_mean is not None:
        gate_kwargs["blank_mean"] = blank_mean
    journey["report"] = gate_video_evidence(journey["video"], **gate_kwargs)


def overlay_text_on_frame(image_path: str, caption: str) -> str:
    """Add text overlay to a frame. Returns path to overlaid image.

    If Pillow unavailable or caption empty, returns original image path.
    Creates a captioned version at <original>-captioned.png
    """
    if not PILLOW_AVAILABLE or not caption or not caption.strip():
        return image_path

    output_path = image_path.replace(".png", "-captioned.png")
    if Path(output_path).exists():
        return output_path

    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        # Try to use a system font; fall back to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Add semi-transparent background for text
        text_color = (255, 255, 255)  # white text
        bg_color = (0, 0, 0, 180)  # semi-transparent black

        # Wrap text to fit width
        max_width = img.width - 40
        lines = []
        words = caption.split()
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width > max_width and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                current_line.append(word)

        if current_line:
            lines.append(" ".join(current_line))

        # Draw background and text
        y = 10
        for line in lines:
            bbox = draw.textbbox((20, y), line, font=font)
            # Draw semi-transparent background
            draw.rectangle(
                [(bbox[0]-5, bbox[1]-5), (bbox[2]+5, bbox[3]+5)],
                fill=bg_color
            )
            draw.text((20, y), line, fill=text_color, font=font)
            y += 40

        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"  [caption overlay] failed: {e}")
        return image_path


def assemble_gif(output_dir: str):
    """Assemble step-*.png screenshots into demo.gif using ffmpeg.

    If captions.json exists, overlay reasoning text on frames.
    """
    pngs = sorted(
        p for p in Path(output_dir).glob("step-*.png")
        if not p.name.endswith("-raw.png") and not p.name.endswith("-captioned.png")
    )
    if not pngs:
        return None

    # Load captions if available
    captions_path = Path(output_dir) / "captions.json"
    captions = {}
    if captions_path.exists():
        try:
            captions = json.loads(captions_path.read_text())
        except (json.JSONDecodeError, IOError):
            pass

    # Apply text overlays if captions available
    frame_paths = []
    for p in pngs:
        caption = captions.get(p.name, "")
        if caption:
            captioned = overlay_text_on_frame(str(p), caption)
            frame_paths.append(Path(captioned))
        else:
            frame_paths.append(p)

    lines = []
    for p in frame_paths[:-1]:  # All frames except the last
        lines.append(f"file '{p}'")
        lines.append("duration 0.8")  # Faster transitions
    # Final frame: hold 3.0s so viewer sees the result clearly
    lines.append(f"file '{frame_paths[-1]}'")
    lines.append("duration 3.0")
    list_path = Path(output_dir) / "frames.txt"
    list_path.write_text("\n".join(lines))

    palette_path = Path(output_dir) / "palette.png"
    gif_path = Path(output_dir) / "demo.gif"

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(list_path),
             "-vf", "scale=960:-2:flags=lanczos,palettegen=max_colors=256:stats_mode=diff",
             str(palette_path)],
            capture_output=True, timeout=60,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(list_path),
             "-i", str(palette_path),
             "-lavfi", "scale=960:-2:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer",
             str(gif_path)],
            capture_output=True, timeout=60,
        )
        if gif_path.exists():
            return str(gif_path)
    except Exception as exc:
        print(f"  [gif] assembly failed: {exc}")
    return None


def assemble_gif_from_video(video_path: str, output_dir: str) -> str | None:
    """Assemble demo.gif directly from a recorded MP4 using ffmpeg.

    Applies the same two-pass palette approach as assemble_gif (palettegen +
    paletteuse), but reads the real recorded video directly instead of
    concatenating per-step screenshots, so the GIF reflects the actual
    recorded run (including timing) instead of a static frame sequence.

    Returns the path to demo.gif on success, or None if the video is
    missing/empty or the ffmpeg conversion fails -- in which case the caller
    should fall back to assemble_gif(output_dir).
    """
    video = Path(video_path)
    if not video.exists() or video.stat().st_size == 0:
        print(f"  [gif] recording missing or empty, falling back to screenshots: {video_path}")
        return None

    palette_path = Path(output_dir) / "video-palette.png"
    gif_path = Path(output_dir) / "demo.gif"
    # Cap width instead of always forcing it, so small recordings aren't upscaled.
    scale_filter = "fps=10,scale='min(960,iw)':-2:flags=lanczos"

    try:
        palette_result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video),
             "-vf", f"{scale_filter},palettegen=max_colors=256:stats_mode=diff",
             str(palette_path)],
            capture_output=True, timeout=240,
        )
        if palette_result.returncode != 0:
            stderr = palette_result.stderr.decode(errors="replace").strip()[-500:]
            print(f"  [gif] palettegen failed for {video_path}: {stderr}")
            return None

        gif_result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video),
             "-i", str(palette_path),
             "-lavfi", f"{scale_filter} [x]; [x][1:v] paletteuse=dither=bayer",
             str(gif_path)],
            capture_output=True, timeout=240,
        )
        if gif_result.returncode != 0:
            stderr = gif_result.stderr.decode(errors="replace").strip()[-500:]
            print(f"  [gif] paletteuse failed for {video_path}: {stderr}")
            return None

        if gif_path.exists():
            return str(gif_path)
    except Exception as exc:
        print(f"  [gif] video-to-gif conversion failed: {exc}")
    return None
