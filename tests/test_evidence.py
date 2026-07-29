"""Tests for the video evidence gate and segmented-recording ffmpeg pipeline.

Synthetic videos are generated with ffmpeg lavfi sources:
- a static single-color video must FAIL the gate (1 distinct screen)
- a multi-scene video must PASS (>= 4 distinct screens, dense frames)
"""
import shutil
import subprocess
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a_test.evidence import EvidenceGateError, gate_video_evidence, verify_video_evidence
from a_test.recording import concat_segments, reencode_cfr

FFMPEG = shutil.which("ffmpeg") is not None
pytestmark = pytest.mark.skipif(not FFMPEG, reason="ffmpeg not on PATH")

COLORS = ["red", "green", "blue", "yellow", "magenta", "cyan"]


def _make_color_video(path, color, seconds=2, fps=30):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"color=c={color}:s=320x240:d={seconds}:r={fps}",
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         str(path)],
        capture_output=True, check=True, timeout=60,
    )


def _make_multi_scene_video(path, seconds_per_scene=1, fps=30):
    """Concatenate 6 different solid-color scenes into one MP4."""
    inputs, filters = [], []
    for i, c in enumerate(COLORS):
        inputs += ["-f", "lavfi", "-i",
                   f"color=c={c}:s=320x240:d={seconds_per_scene}:r={fps}"]
        filters.append(f"[{i}:v]")
    filtergraph = "".join(filters) + f"concat=n={len(COLORS)}:v=1:a=0[out]"
    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", filtergraph,
         "-map", "[out]", "-c:v", "libx264", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", str(path)],
        capture_output=True, check=True, timeout=120,
    )


def _duration(path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, timeout=30,
    ).stdout.decode().strip()
    return float(out)


def test_static_video_fails_gate(tmp_path):
    """A single static screen is exactly the founder-rejected failure mode."""
    video = tmp_path / "static.mp4"
    _make_color_video(video, "red", seconds=6)
    report = verify_video_evidence(str(video))
    assert report["verdict"] == "fail"
    assert report["distinct_count"] < 4
    assert any("distinct" in f for f in report["failures"])


def test_black_video_fails_gate(tmp_path):
    video = tmp_path / "black.mp4"
    _make_color_video(video, "black", seconds=4)
    report = verify_video_evidence(str(video))
    assert report["verdict"] == "fail"
    assert any("blank" in f for f in report["failures"])


def test_multi_scene_video_passes_gate(tmp_path):
    video = tmp_path / "journey.mp4"
    _make_multi_scene_video(video)
    report_path = tmp_path / "report.json"
    report = verify_video_evidence(str(video), report_path=str(report_path))
    assert report["verdict"] == "pass", report["failures"]
    assert report["distinct_count"] >= 4
    assert report_path.exists()
    assert len(report["frames"]) == 6
    assert all(f["hash"] for f in report["frames"])


def test_missing_video_fails_gate(tmp_path):
    report = verify_video_evidence(str(tmp_path / "nope.mp4"))
    assert report["verdict"] == "fail"


def test_gate_raises_on_failure(tmp_path):
    video = tmp_path / "static.mp4"
    _make_color_video(video, "blue", seconds=4)
    with pytest.raises(EvidenceGateError) as exc:
        gate_video_evidence(str(video))
    assert exc.value.report["verdict"] == "fail"


def test_gate_passes_returns_report(tmp_path):
    video = tmp_path / "journey.mp4"
    _make_multi_scene_video(video)
    report = gate_video_evidence(str(video))
    assert report["verdict"] == "pass"


def test_reencode_cfr_densifies_sparse_video(tmp_path):
    """A sparse (low-fps) source becomes a dense 30fps CFR encode."""
    sparse = tmp_path / "sparse.mp4"
    _make_color_video(sparse, "red", seconds=4, fps=2)  # 8 frames total
    cfr = tmp_path / "cfr.mp4"
    assert reencode_cfr(str(sparse), str(cfr), fps=30)
    report = verify_video_evidence(str(cfr), min_distinct=1)
    # frame-density check (a) must now pass: nb_frames >= duration*fps*0.5
    assert not any("frame-starved" in f for f in report["failures"])
    assert report["nb_frames"] >= report["duration"] * 30 * 0.5


def test_concat_segments_and_speedup(tmp_path):
    """Two segments concat cleanly (no DTS errors) and speedup shortens output."""
    segs = []
    for i, c in enumerate(["red", "green"]):
        seg = tmp_path / f"seg{i}.mp4"
        _make_color_video(seg, c, seconds=3)
        segs.append(str(seg))

    plain = tmp_path / "plain.mp4"
    assert concat_segments(segs, str(plain), fps=30)
    assert abs(_duration(plain) - 6.0) < 0.5

    fast = tmp_path / "fast.mp4"
    assert concat_segments(segs, str(fast), fps=30, speedup=3.0)
    assert abs(_duration(fast) - 2.0) < 0.5
    # sped-up output must still be frame-dense (CFR), not a slideshow
    report = verify_video_evidence(str(fast), min_distinct=2)
    assert not any("frame-starved" in f for f in report["failures"])


def test_concat_segments_skips_missing(tmp_path):
    seg = tmp_path / "seg0.mp4"
    _make_color_video(seg, "red", seconds=2)
    out = tmp_path / "out.mp4"
    assert concat_segments([str(seg), str(tmp_path / "ghost.mp4")], str(out), fps=30)
    assert abs(_duration(out) - 2.0) < 0.5


def test_concat_segments_empty_list(tmp_path):
    assert not concat_segments([], str(tmp_path / "out.mp4"))


def test_dark_but_structured_frame_is_not_blank(tmp_path):
    """A dark-themed app must not be reported as an all-black frame.

    The tarot demo UI renders at a mean luma of ~15, below the old hard
    _BLANK_MEAN cutoff, so every frame of a perfectly good recording was
    flagged blank. Only near-UNIFORM frames are actually worthless.
    """
    import subprocess
    video = tmp_path / "dark.mp4"
    # A dark but clearly structured scene: moving white box on a near-black bg.
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-f", "lavfi", "-i", "color=c=0x0a0a12:s=256x256:d=4:r=30",
        "-f", "lavfi", "-i", "color=c=white:s=48x48:d=4:r=30",
        "-filter_complex", "[0][1]overlay=x='t*40':y='t*40'",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video),
    ], capture_output=True, timeout=120, check=True)

    report = verify_video_evidence(str(video), frames=6, min_distinct=3)
    blanks = [f for f in report["frames"] if f["blank"]]
    assert not blanks, f"dark-but-structured frames wrongly flagged blank: {blanks}"


def test_segmented_recorder_passes_size_and_bitrate():
    """size/bitrate must reach the screenrecord invocation.

    Native-resolution capture on a loaded host starves the on-device encoder
    into a slideshow; downscaling is the documented mitigation, so the plumbing
    is worth asserting.
    """
    from a_test.recording import SegmentedRecorder
    rec = SegmentedRecorder("j", "/tmp", size="720x1600", bitrate=4_000_000)
    cmd = rec._screenrecord_cmd("/sdcard/x.mp4")
    assert "--size 720x1600" in cmd
    assert "--bit-rate 4000000" in cmd

    plain = SegmentedRecorder("j", "/tmp")._screenrecord_cmd("/sdcard/x.mp4")
    assert "--size" not in plain and "--bit-rate" not in plain
