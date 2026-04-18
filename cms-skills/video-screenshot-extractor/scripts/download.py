#!/usr/bin/env python3
"""
download.py — fetch a video + auto-generated captions via yt-dlp.

Produces <out> (the MP4 file) and, when captions are available, a sibling .vtt
file with the same stem. Callers that don't find the .vtt should treat the
transcript as unavailable and fall back to proximity-only frame matching.

Usage:
  python3 download.py --url <video_url> --out <path/to/video.mp4>
"""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys


def run_ytdlp(url: str, out_path: pathlib.Path) -> None:
    """Download the best available MP4 into out_path, plus auto-subs if present."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # yt-dlp's --output takes a template. We strip the extension and let yt-dlp
    # add the right one per file type (video + subs each get their own ext).
    stem = out_path.with_suffix("")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        # Best MP4 that doesn't require re-encoding. Falls back to best single file.
        "--format", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "--merge-output-format", "mp4",
        "--write-auto-subs",
        "--write-subs",
        "--sub-langs", "en.*,en",
        "--sub-format", "vtt",
        "--convert-subs", "vtt",
        "--no-warnings",
        "--output", f"{stem}.%(ext)s",
        url,
    ]

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.exit("ERROR: yt-dlp not installed. Run preflight.sh first.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"ERROR: yt-dlp failed with exit code {e.returncode}. "
                 "Check URL availability, geo-restrictions, and privacy.")

    # yt-dlp may output an unexpected extension if the best format isn't MP4.
    # Locate the actual video file and rename to the requested path if needed.
    candidates = sorted(stem.parent.glob(f"{stem.name}.*"))
    video_exts = {".mp4", ".mkv", ".webm", ".mov"}
    video_files = [c for c in candidates if c.suffix.lower() in video_exts]
    if not video_files:
        sys.exit("ERROR: yt-dlp produced no recognizable video file.")
    actual = video_files[0]
    if actual != out_path:
        shutil.move(str(actual), str(out_path))

    # Report VTT path if present for caller convenience.
    vtt_candidates = list(stem.parent.glob(f"{stem.name}.*.vtt")) + \
                     list(stem.parent.glob(f"{stem.name}.vtt"))
    if vtt_candidates:
        # Normalize to <stem>.vtt for deterministic downstream lookup.
        target_vtt = stem.with_suffix(".vtt")
        if vtt_candidates[0] != target_vtt:
            shutil.move(str(vtt_candidates[0]), str(target_vtt))
        print(f"VIDEO: {out_path}")
        print(f"TRANSCRIPT: {target_vtt}")
    else:
        print(f"VIDEO: {out_path}")
        print("TRANSCRIPT: (none)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--url", required=True, help="Source video URL.")
    ap.add_argument("--out", required=True, help="Output MP4 path.")
    args = ap.parse_args()

    out_path = pathlib.Path(args.out).resolve()
    run_ytdlp(args.url, out_path)


if __name__ == "__main__":
    main()
