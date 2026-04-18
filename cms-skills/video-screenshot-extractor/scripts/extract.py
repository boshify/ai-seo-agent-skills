#!/usr/bin/env python3
"""
extract.py — extract a single full-quality PNG frame from a video at a given
timestamp, using the raw video stream (no player overlays, no pause icons, no
progress bars).

Usage:
  python3 extract.py --video <path> --ts <HH:MM:SS|MM:SS|seconds> --out <png_path>
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys


def normalize_timestamp(ts: str) -> str:
    """Accept HH:MM:SS, MM:SS, or raw seconds. Return an ffmpeg-compatible string."""
    ts = ts.strip()
    if ":" in ts:
        parts = ts.split(":")
        if len(parts) == 2:
            return f"00:{parts[0].zfill(2)}:{parts[1]}"
        if len(parts) == 3:
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2]}"
    # Raw seconds (float or int) — ffmpeg handles this directly.
    return ts


def extract_frame(video: str, ts: str, out: pathlib.Path) -> None:
    """Extract one lossless PNG frame at the given timestamp."""
    out.parent.mkdir(parents=True, exist_ok=True)

    # -ss before -i: fast seek (keyframe-accurate, very fast)
    # -ss after -i would be frame-accurate but much slower on long videos.
    # For screen recordings with frequent keyframes, the fast-seek inaccuracy
    # is typically <200ms which is imperceptible for still frames.
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-ss", ts,
        "-i", video,
        "-frames:v", "1",
        "-c:v", "png",
        "-compression_level", "0",
        "-q:v", "1",
        "-y",
        str(out),
    ]

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.exit("ERROR: ffmpeg not installed.")
    except subprocess.CalledProcessError as e:
        # Retry once with a 500ms later offset — seek at exact boundaries can fail
        # on some codecs.
        try:
            offset_ts = f"{ts}+0.5" if ":" not in ts else ts  # crude bump for plain seconds
            cmd[4] = offset_ts if ":" not in ts else ts
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            sys.exit(f"ERROR: ffmpeg failed to extract frame at {ts}: {e}")

    if not out.exists() or out.stat().st_size == 0:
        sys.exit(f"ERROR: frame extraction produced no output at {out}.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--video", required=True, help="Local video file path.")
    ap.add_argument("--ts", required=True, help="Timestamp: HH:MM:SS, MM:SS, or seconds.")
    ap.add_argument("--out", required=True, help="Output PNG path.")
    args = ap.parse_args()

    ts = normalize_timestamp(args.ts)
    extract_frame(args.video, ts, pathlib.Path(args.out).resolve())
    print(f"OK: {args.out}")


if __name__ == "__main__":
    main()
