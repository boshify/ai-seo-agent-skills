#!/usr/bin/env bash
# Dependency preflight for video-screenshot-extractor.
#
# Portability contract: this script runs on any Unix-like shell. It makes no
# assumptions about OS, container, or path layout. It only verifies or installs
# dependencies that can be installed without system privileges. ffmpeg is the
# only hard requirement that cannot be auto-installed reliably — the script
# stops and prints platform-specific install instructions if it's missing.

set -eu

RED=$'\033[31m'
YELLOW=$'\033[33m'
GREEN=$'\033[32m'
RESET=$'\033[0m'

fail=0

echo "==> Checking ffmpeg..."
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "${RED}FATAL: ffmpeg is required and cannot be auto-installed.${RESET}"
  echo "Install via:"
  echo "  macOS:   brew install ffmpeg"
  echo "  Debian:  sudo apt-get install -y ffmpeg"
  echo "  RHEL:    sudo dnf install -y ffmpeg"
  echo "  Windows: choco install ffmpeg"
  fail=1
else
  echo "${GREEN}ffmpeg present:${RESET} $(ffmpeg -version | head -n 1)"
fi

echo "==> Checking yt-dlp..."
if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp not found — installing via pip..."
  if command -v pip3 >/dev/null 2>&1; then
    pip3 install --user --quiet yt-dlp || { echo "${RED}pip install yt-dlp failed${RESET}"; fail=1; }
  elif command -v pip >/dev/null 2>&1; then
    pip install --user --quiet yt-dlp || { echo "${RED}pip install yt-dlp failed${RESET}"; fail=1; }
  else
    echo "${RED}FATAL: neither pip3 nor pip available. Install Python 3.8+ with pip.${RESET}"
    fail=1
  fi

  # After install, yt-dlp may not be on PATH — this is especially common on
  # Windows, where pip's --user scripts directory is not on PATH by default.
  if [ "$fail" -eq 0 ] && ! command -v yt-dlp >/dev/null 2>&1; then
    case "${OSTYPE:-}" in
      msys*|cygwin*|win32*)
        guess="$(python -c 'import site; print(site.USER_BASE)' 2>/dev/null)/Scripts"
        echo "${YELLOW}WARN: yt-dlp installed but not on PATH (common on Windows).${RESET}"
        echo "  Add this directory to PATH:"
        echo "    ${guess}"
        echo "  For the current shell:  export PATH=\"${guess//\\/\/}:\$PATH\""
        echo "  Permanently (PowerShell): [Environment]::SetEnvironmentVariable('Path', \"\$env:Path;${guess}\", 'User')"
        fail=1
        ;;
      *)
        guess="$(python3 -c 'import site; print(site.USER_BASE)' 2>/dev/null)/bin"
        echo "${YELLOW}WARN: yt-dlp installed but not on PATH.${RESET}"
        echo "  Add this to PATH: ${guess}"
        echo "  For the current shell: export PATH=\"${guess}:\$PATH\""
        fail=1
        ;;
    esac
  fi
else
  echo "${GREEN}yt-dlp present:${RESET} $(yt-dlp --version)"
fi

echo "==> Checking exiftool..."
if ! command -v exiftool >/dev/null 2>&1; then
  echo "${YELLOW}WARN: exiftool not present. Falling back to piexif + Pillow for EXIF writing.${RESET}"
  echo "  (Optional install: brew install exiftool | apt-get install libimage-exiftool-perl)"
else
  echo "${GREEN}exiftool present:${RESET} $(exiftool -ver)"
fi

echo "==> Checking Python libraries (Pillow, piexif)..."
if ! python3 -c "import PIL" >/dev/null 2>&1; then
  echo "Pillow not found — installing via pip..."
  python3 -m pip install --user --quiet Pillow || { echo "${RED}pip install Pillow failed${RESET}"; fail=1; }
fi
if ! python3 -c "import piexif" >/dev/null 2>&1; then
  echo "piexif not found — installing via pip..."
  python3 -m pip install --user --quiet piexif || { echo "${RED}pip install piexif failed${RESET}"; fail=1; }
fi

if [ "$fail" -eq 0 ]; then
  python3 -c "import PIL, piexif" >/dev/null 2>&1 && echo "${GREEN}Pillow + piexif present.${RESET}"
fi

if [ "$fail" -ne 0 ]; then
  echo ""
  echo "${RED}Preflight failed. Resolve the items above and re-run.${RESET}"
  exit 1
fi

echo ""
echo "${GREEN}Preflight OK. All required dependencies available.${RESET}"
