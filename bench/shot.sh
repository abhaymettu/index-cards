#!/bin/sh
# Render an SVG to a 2x PNG with headless Chrome (separate profile): shot.sh in.svg out.png
svg=$1; out=$2
w=$(grep -o "width='[0-9]*'" "$svg" | head -1 | tr -dc 0-9)
h=$(grep -o "height='[0-9]*'" "$svg" | head -1 | tr -dc 0-9)
prof=$(mktemp -d)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --user-data-dir="$prof" --disable-gpu \
  --hide-scrollbars --force-device-scale-factor=2 --window-size="$w,$h" --screenshot="$out" "file://$(cd "$(dirname "$svg")" && pwd)/$(basename "$svg")" 2>/dev/null
rm -rf "$prof"
