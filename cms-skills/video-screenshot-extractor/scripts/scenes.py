#!/usr/bin/env python3
"""
scenes.py — run ffmpeg scene-change detection over a video and print candidate
timestamps (one per line, in seconds with millisecond precision).

For a 10-minute screen recording at threshold 0.3, this typically yields 30-80
candidates. Lower threshold = more candidates. Higher threshold = fewer.

Tuning guidance:
  - 0.3 is a safe default for screen recordings with sharp cuts (Jonathan's
    proof videos, most talking-head-plus-slides formats).
  - 0.2 catches softer transitions (fades, zoom-ins, slower reveals) at the
    cost of more false positives.
  - 0.4+ only for videos dominated by abrupt cuts.

If fewer than --min-candidates timestamps come back at the chosen threshold,
the script auto-retries at a lower threshold (0.2, then 0.15). This prevents
the caller from having to second-guess the tuning when a video has unusually
smooth transitions. Disable with --no-retry.

Usage:
  python3 scenes.py --video <path> [--threshold 0.3] [--min-candidates 5] [--no-retry]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys


SHOWINFO_RE = re.compile(r"pts_time:(\d+\.\d+)")


def detect_scenes(video_path: str, threshold: float) -> list[float]:
    """Return a list of scene-change timestamps in seconds."""
    # -vf select=gt(scene,T) emits frames where scene-score > T.
    # showinfo prints a log line per frame containing pts_time.
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i", video_path,
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null",
        "-",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit("ERROR: ffmpeg not installed.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"ERROR: ffmpeg scene detection failed: {e.stderr[-500:]}")

    timestamps = [float(m) for m in SHOWINFO_RE.findall(proc.stderr)]
    return sorted(set(timestamps))


def detect_with_retry(video_path: str, threshold: float, min_candidates: int,
                      allow_retry: bool) -> tuple[list[float], float]:
    """Detect scenes; if the primary threshold yields too few, step down."""
    fallback_chain = [threshold]
    if allow_retry:
        for t in (0.2, 0.15):
            if t < threshold and t not in fallback_chain:
                fallback_chain.append(t)

    last = []
    used = threshold
    for t in fallback_chain:
        last = detect_scenes(video_path, t)
        used = t
        if len(last) >= min_candidates:
            break
        if allow_retry:
            print(f"# {len(last)} candidates at threshold {t} — retrying lower", file=sys.stderr)
    return last, used


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--video", required=True, help="Local video file path.")
    ap.add_argument("--threshold", type=float, default=0.3,
                    help="Scene-change sensitivity (0.0-1.0). Lower = more candidates.")
    ap.add_argument("--min-candidates", type=int, default=5,
                    help="Minimum candidates before auto-retrying at a lower threshold.")
    ap.add_argument("--no-retry", action="store_true",
                    help="Disable automatic threshold step-down.")
    args = ap.parse_args()

    timestamps, used = detect_with_retry(
        args.video, args.threshold, args.min_candidates, not args.no_retry
    )
    print(f"# threshold_used={used} candidates={len(timestamps)}", file=sys.stderr)
    for t in timestamps:
        print(f"{t:.3f}")


if __name__ == "__main__":
    main()
