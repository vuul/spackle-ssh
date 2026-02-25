#!/usr/bin/env bash
#
# build_app.sh — Build Spackle.app using py2app
#
# Usage: ./build_app.sh
# Output: dist/Spackle.app
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv_build"
ICON_PNG="src/spackle/resources/Spackle-icon.png"
ICON_ICNS="Spackle.icns"
ICONSET_DIR="Spackle.iconset"

echo "==> Creating build virtualenv..."
python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> Installing py2app..."
pip install --quiet py2app

echo "==> Generating .icns icon from $ICON_PNG..."
rm -rf "$ICONSET_DIR"
mkdir "$ICONSET_DIR"

# Generate all required icon sizes from the source PNG.
# sips will scale up if the source is smaller than the target; the image
# may look slightly soft at the largest sizes but remains usable.
for size in 16 32 64 128 256 512; do
    sips -z "$size" "$size" "$ICON_PNG" --out "$ICONSET_DIR/icon_${size}x${size}.png" >/dev/null 2>&1
done
# Retina variants (@2x): each is double the nominal size
for size in 16 32 128 256; do
    double=$((size * 2))
    cp "$ICONSET_DIR/icon_${double}x${double}.png" "$ICONSET_DIR/icon_${size}x${size}@2x.png"
done
# 512@2x = 1024, generate it even though source is small
sips -z 1024 1024 "$ICON_PNG" --out "$ICONSET_DIR/icon_512x512@2x.png" >/dev/null 2>&1

iconutil -c icns "$ICONSET_DIR" -o "$ICON_ICNS"
rm -rf "$ICONSET_DIR"
echo "    Created $ICON_ICNS"

echo "==> Building Spackle.app with py2app..."
python setup.py py2app 2>&1 | tail -5

echo "==> Cleaning up build artifacts..."
deactivate
rm -rf "$VENV_DIR" build
rm -f "$ICON_ICNS"

echo ""
echo "==> Done! Application bundle is at:"
echo "    $(pwd)/dist/Spackle.app"
echo ""
echo "    Open it with:  open dist/Spackle.app"
