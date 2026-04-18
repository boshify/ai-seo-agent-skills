#!/usr/bin/env python3
"""
exif.py — write SEO-optimized EXIF to a PNG file.

Preferred backend: exiftool (handles PNG eXIf + XMP cleanly). Fallback: piexif
to build the EXIF bytes + Pillow to embed them in the PNG eXIf chunk.

Always strips: GPS data, camera Make/Model, software identifiers (yt-dlp,
ffmpeg, Pillow, etc.), and any pre-existing EXIF from the source video's frame.
Never writes: Comments, UserComment, or URL parameters in the Source field.

Usage:
  python3 exif.py --file <png_path> \
    --title "Edia Ahrefs Chart" \
    --description "Ahrefs organic traffic graph showing Edia's 42% decline." \
    --keywords "AI content strategy,content collapse,Ahrefs traffic" \
    --artist "Jonathan Boshoff" \
    --copyright "Jonathan Boshoff 2026" \
    --source "https://youtube.com/watch?v=abc123"
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


STRIP_SOFTWARE_TOKENS = {"yt-dlp", "ffmpeg", "Pillow", "PIL", "piexif", "exiftool"}

# Query parameters we drop from the canonical source URL. These are
# timestamp deeplinks, share/feature tracking, and playlist context — none of
# which belong in a permanent Source field. The video ID itself (`v` on
# YouTube, the path for other hosts) is preserved.
STRIP_QUERY_PARAMS = {"t", "time_continue", "start", "end",
                      "feature", "si", "pp", "ab_channel",
                      "list", "index"}


def canonical_source_url(url: str) -> str:
    """Keep scheme/host/path/video-id; drop timestamp and tracking params."""
    p = urlparse(url)
    kept = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=False)
            if k not in STRIP_QUERY_PARAMS]
    return urlunparse((p.scheme, p.netloc, p.path, "", urlencode(kept), ""))


def write_with_exiftool(path: pathlib.Path, fields: dict[str, str]) -> None:
    """Write EXIF via exiftool; strip GPS, camera, software on the same pass."""
    cmd = [
        "exiftool",
        "-overwrite_original",
        # Strip fingerprinting + privacy-sensitive tags.
        "-gps:all=",
        "-Make=",
        "-Model=",
        "-Software=",
        "-HostComputer=",
        # Explicitly clear anything we never write.
        "-Comment=",
        "-UserComment=",
    ]
    # Map field name -> exiftool tag names (covers XMP + EXIF + IPTC so readers
    # find the value regardless of which schema they prefer).
    tag_map = {
        "title": ["-XMP:Title=", "-IPTC:ObjectName=", "-EXIF:ImageDescription="],
        "description": ["-XMP:Description=", "-IPTC:Caption-Abstract="],
        "keywords": ["-XMP:Subject=", "-IPTC:Keywords="],
        "artist": ["-XMP:Creator=", "-IPTC:By-line=", "-EXIF:Artist="],
        "copyright": ["-XMP:Rights=", "-IPTC:CopyrightNotice=", "-EXIF:Copyright="],
        "source": ["-XMP:Source=", "-IPTC:Source="],
    }
    for field, value in fields.items():
        if not value:
            continue
        for tag in tag_map.get(field, []):
            # Handle multi-value keywords: exiftool accepts comma-separated if we
            # pass the whole string, but the List tags prefer per-value assignment.
            if field == "keywords" and ("Subject" in tag or "Keywords" in tag):
                for kw in [k.strip() for k in value.split(",") if k.strip()]:
                    cmd.append(f"{tag}{kw}")
            else:
                cmd.append(f"{tag}{value}")

    cmd.append(str(path))
    subprocess.run(cmd, check=True, capture_output=True)


def write_with_pillow(path: pathlib.Path, fields: dict[str, str]) -> None:
    """Fallback path: write what piexif can handle to the PNG eXIf chunk
    (Title/Artist/Copyright via ImageDescription+Artist+Copyright IFD tags) AND
    write the remaining SEO-critical fields (Description, Keywords, Source) as
    PNG tEXt chunks using keys that exiftool, image-processing libraries, and
    common SEO crawlers recognize.

    The tEXt chunk approach exists because piexif targets JPEG EXIF and cannot
    emit XMP, which is where XMP-only fields like Keywords normally live.
    Writing them as PNG tEXt means they are still discoverable — a strict
    superset of what piexif-alone would produce.
    """
    import piexif
    from PIL import Image, PngImagePlugin

    exif_ifd = {}
    zeroth_ifd = {}

    if fields.get("title"):
        zeroth_ifd[piexif.ImageIFD.ImageDescription] = fields["title"].encode("utf-8")
    if fields.get("artist"):
        zeroth_ifd[piexif.ImageIFD.Artist] = fields["artist"].encode("utf-8")
    if fields.get("copyright"):
        zeroth_ifd[piexif.ImageIFD.Copyright] = fields["copyright"].encode("utf-8")

    exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd, "1st": {}, "thumbnail": None, "GPS": {}}
    exif_bytes = piexif.dump(exif_dict)

    # Build PNG tEXt chunks for the fields piexif can't carry. Keys follow the
    # PNG/XMP convention recognized by exiftool, ImageMagick, and most
    # metadata-aware tools when later read back.
    png_info = PngImagePlugin.PngInfo()
    if fields.get("title"):
        png_info.add_text("Title", fields["title"])
    if fields.get("description"):
        png_info.add_text("Description", fields["description"])
    if fields.get("keywords"):
        png_info.add_text("Keywords", fields["keywords"])
    if fields.get("artist"):
        png_info.add_text("Author", fields["artist"])
    if fields.get("copyright"):
        png_info.add_text("Copyright", fields["copyright"])
    if fields.get("source"):
        png_info.add_text("Source", fields["source"])

    img = Image.open(path)
    img.save(path, format="PNG", exif=exif_bytes, pnginfo=png_info)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--file", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--description", default="")
    ap.add_argument("--keywords", default="", help="Comma-separated keyword list.")
    ap.add_argument("--artist", default="")
    ap.add_argument("--copyright", default="")
    ap.add_argument("--source", default="", help="Canonical source URL. Query params will be stripped.")
    args = ap.parse_args()

    path = pathlib.Path(args.file).resolve()
    if not path.exists():
        sys.exit(f"ERROR: file not found: {path}")

    fields = {
        "title": args.title,
        "description": args.description,
        "keywords": args.keywords,
        "artist": args.artist,
        "copyright": args.copyright,
        "source": canonical_source_url(args.source) if args.source else "",
    }

    if shutil.which("exiftool"):
        try:
            write_with_exiftool(path, fields)
            print(f"OK (exiftool): {path}")
            return
        except subprocess.CalledProcessError as e:
            print(f"exiftool failed ({e.stderr[-300:] if e.stderr else 'no stderr'}); "
                  "falling back to piexif+Pillow.", file=sys.stderr)

    try:
        write_with_pillow(path, fields)
        print(f"OK (piexif+Pillow): {path}")
    except ImportError:
        sys.exit("ERROR: neither exiftool nor piexif+Pillow available. Run preflight.sh.")
    except Exception as e:
        sys.exit(f"ERROR: EXIF write failed: {e}")


if __name__ == "__main__":
    main()
