"""Video evidence gate for a-test recordings.

Verifies that a recorded video actually shows a multi-step user journey
before it is shipped anywhere (YouTube, PR comment, release notes).

Motivation: `adb screenrecord` emits frames only on screen change (variable
framerate). A 177s session can yield 67 frames; after a 10x speedup that is a
3.6s slideshow that looks like a static picture. Nothing previously asserted
the video showed distinct screens, so broken recordings shipped.

The gate FAILS a video if:
  a) frame count < duration * fps * 0.5  (starved/variable-framerate encode)
  b) fewer than `min_distinct` visually distinct screens among K evenly
     spaced sampled frames (perceptual average-hash, hamming distance)
  c) any sampled frame is blank (all-black / near-uniform)

It returns (and optionally writes) a machine-readable report:
  {"verdict": "pass"|"fail", "failures": [...], "duration": ..., "fps": ...,
   "nb_frames": ..., "distinct_count": ..., "frames": [{"t": ..., "hash": ...,
   "mean": ..., "blank": ...}, ...]}

Only requires ffmpeg/ffprobe on PATH -- frames are sampled as 16x16 grayscale
rawvideo bytes, so no Pillow/numpy dependency.
"""
import json
import subprocess
from pathlib import Path

# 16x16 grayscale sample -> 256-bit average hash per frame.
_HASH_SIZE = 16
_HASH_BITS = _HASH_SIZE * _HASH_SIZE
# Frames whose hashes differ in <= this many bits are "the same screen".
_SIMILARITY_BITS = int(_HASH_BITS * 0.10)  # 10% of bits
# ...unless their mean luma differs by more than this (aHash is blind to
# uniform frames -- every solid color hashes to 0).
_SIMILARITY_MEAN_DELTA = 10.0
# Mean luma below this (0-255) marks a frame as blank/black.
_BLANK_MEAN = 16.0
# Near-uniform AND near-white (blank page / white flash) is also blank.
_WHITE_MEAN = 245.0
_UNIFORM_VARIANCE = 4.0


class EvidenceGateError(AssertionError):
    """Raised when a video fails the evidence gate. Carries the report."""

    def __init__(self, report: dict):
        self.report = report
        super().__init__("video evidence gate failed: " + "; ".join(report.get("failures", [])))


def _ffprobe_stats(video_path: str) -> tuple[float, float, int]:
    """Return (duration_seconds, fps, nb_frames) for the video's first stream."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-count_packets",
         "-show_entries", "stream=r_frame_rate,nb_read_packets:format=duration",
         "-of", "json", video_path],
        capture_output=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.decode(errors='replace').strip()[-300:]}")
    data = json.loads(result.stdout.decode())
    duration = float(data.get("format", {}).get("duration", 0) or 0)
    stream = (data.get("streams") or [{}])[0]
    rate = stream.get("r_frame_rate", "0/1")
    try:
        num, den = rate.split("/")
        fps = float(num) / float(den) if float(den) else 0.0
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    nb_frames = int(stream.get("nb_read_packets", 0) or 0)
    return duration, fps, nb_frames


def _sample_frame_gray(video_path: str, timestamp: float) -> bytes:
    """Extract one frame at `timestamp` as HASH_SIZE x HASH_SIZE grayscale raw bytes."""
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{timestamp:.3f}", "-i", video_path,
         "-frames:v", "1",
         "-vf", f"scale={_HASH_SIZE}:{_HASH_SIZE}", "-pix_fmt", "gray",
         "-f", "rawvideo", "-"],
        capture_output=True, timeout=60,
    )
    if result.returncode != 0 or len(result.stdout) < _HASH_BITS:
        return b""
    return result.stdout[:_HASH_BITS]


def _average_hash(pixels: bytes) -> int:
    """256-bit average hash: bit i set iff pixel i is above the mean luma."""
    mean = sum(pixels) / len(pixels)
    bits = 0
    for i, p in enumerate(pixels):
        if p > mean:
            bits |= 1 << i
    return bits


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _same_screen(a: tuple, b: tuple) -> bool:
    """Signatures are (ahash, mean_luma); near-identical on both axes = same screen."""
    return (_hamming(a[0], b[0]) <= _SIMILARITY_BITS
            and abs(a[1] - b[1]) <= _SIMILARITY_MEAN_DELTA)


def _distinct_count(signatures: list) -> int:
    """Greedy clustering: count screens that differ from every one already seen."""
    representatives: list = []
    for sig in signatures:
        if all(not _same_screen(sig, r) for r in representatives):
            representatives.append(sig)
    return len(representatives)


def verify_video_evidence(
    video_path: str,
    frames: int = 6,
    min_distinct: int = 4,
    min_frame_ratio: float = 0.5,
    report_path: str | None = None,
) -> dict:
    """Gate a video: sample `frames` evenly spaced frames, verify real motion.

    Returns a machine-readable report dict with verdict "pass" or "fail".
    Never raises on a failing video -- use gate_video_evidence() to raise.
    Writes the report to `report_path` as JSON when given.
    """
    failures: list[str] = []
    frame_reports: list[dict] = []
    duration = fps = 0.0
    nb_frames = 0
    distinct = 0

    video = Path(video_path)
    if not video.exists() or video.stat().st_size == 0:
        failures.append(f"video missing or empty: {video_path}")
    else:
        try:
            duration, fps, nb_frames = _ffprobe_stats(video_path)
        except (RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
            failures.append(f"ffprobe failed: {exc}")

    if not failures:
        # (a) starved encode: variable-framerate sources emit frames only on
        # screen change, producing a slideshow after CFR-naive speedups.
        expected = duration * fps * min_frame_ratio
        if duration <= 0:
            failures.append("zero duration")
        elif fps > 0 and nb_frames < expected:
            failures.append(
                f"frame-starved video: {nb_frames} frames < {expected:.0f} "
                f"(duration {duration:.1f}s * {fps:.1f}fps * {min_frame_ratio})"
            )

        signatures: list = []
        for i in range(frames):
            t = duration * (i + 0.5) / frames
            pixels = _sample_frame_gray(video_path, t)
            if not pixels:
                frame_reports.append({"t": round(t, 3), "hash": None, "mean": None, "blank": True})
                failures.append(f"could not decode frame at {t:.1f}s")
                continue
            mean = sum(pixels) / len(pixels)
            variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
            blank = mean < _BLANK_MEAN or (mean > _WHITE_MEAN and variance < _UNIFORM_VARIANCE)
            h = _average_hash(pixels)
            signatures.append((h, mean))
            frame_reports.append({
                "t": round(t, 3),
                "hash": f"{h:064x}",
                "mean": round(mean, 1),
                "blank": blank,
            })
            if blank:
                # (c) blank/black frame
                failures.append(f"blank frame at {t:.1f}s (mean luma {mean:.0f})")

        # (b) not enough distinct screens => static picture / broken journey
        distinct = _distinct_count(signatures)
        if distinct < min_distinct:
            failures.append(
                f"only {distinct} distinct screen(s) across {len(signatures)} sampled "
                f"frames; need >= {min_distinct} for a multi-step journey"
            )

    report = {
        "video": str(video_path),
        "verdict": "fail" if failures else "pass",
        "failures": failures,
        "duration": round(duration, 3),
        "fps": round(fps, 3),
        "nb_frames": nb_frames,
        "sampled_frames": frames,
        "distinct_count": distinct,
        "min_distinct": min_distinct,
        "frames": frame_reports,
    }

    if report_path:
        Path(report_path).write_text(json.dumps(report, indent=2))

    return report


def gate_video_evidence(video_path: str, **kwargs) -> dict:
    """Like verify_video_evidence, but raises EvidenceGateError on failure.

    Call this BEFORE any upload step in a scenario:

        report = gate_video_evidence("final.mp4", report_path="report.json")
        upload_to_youtube("final.mp4")  # only reached if the gate passed
    """
    report = verify_video_evidence(video_path, **kwargs)
    if report["verdict"] != "pass":
        raise EvidenceGateError(report)
    return report
