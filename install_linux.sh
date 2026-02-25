#!/usr/bin/env bash
#
# install_linux.sh — Install Spackle for the current user on Linux
#
# Usage: ./install_linux.sh
# Installs to ~/.local/ (no sudo required)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons"
APP_DIR="$HOME/.local/share/applications"

ICON_SRC="$SCRIPT_DIR/src/spackle/resources/Spackle-icon.png"
SCRIPT_SRC="$SCRIPT_DIR/spackle.py"
DESKTOP_SRC="$SCRIPT_DIR/spackle.desktop"

# ── Dependency checks ────────────────────────────────────────────────
missing=0

if ! command -v python3 &>/dev/null; then
    echo "WARNING: python3 not found."
    echo "  Debian/Ubuntu: sudo apt install python3"
    echo "  Fedora:        sudo dnf install python3"
    echo ""
    missing=1
fi

if ! python3 -c "import tkinter" &>/dev/null 2>&1; then
    echo "WARNING: tkinter not found."
    echo "  Debian/Ubuntu: sudo apt install python3-tk"
    echo "  Fedora:        sudo dnf install python3-tkinter"
    echo ""
    missing=1
fi

if ! command -v xterm &>/dev/null; then
    echo "WARNING: xterm not found (required for terminal sessions on Linux)."
    echo "  Debian/Ubuntu: sudo apt install xterm"
    echo "  Fedora:        sudo dnf install xterm"
    echo ""
    missing=1
fi

if [ "$missing" -eq 1 ]; then
    echo "Install the missing dependencies above, then re-run this script."
    exit 1
fi

# ── Install ──────────────────────────────────────────────────────────
echo "==> Installing Spackle to ~/.local/ ..."

mkdir -p "$BIN_DIR" "$ICON_DIR" "$APP_DIR"

echo "    Copying spackle.py -> $BIN_DIR/spackle"
cp "$SCRIPT_SRC" "$BIN_DIR/spackle"
chmod +x "$BIN_DIR/spackle"

echo "    Copying icon -> $ICON_DIR/spackle.png"
cp "$ICON_SRC" "$ICON_DIR/spackle.png"

echo "    Installing desktop launcher -> $APP_DIR/spackle.desktop"
sed \
    -e "s|^Exec=.*|Exec=$BIN_DIR/spackle|" \
    -e "s|^Icon=.*|Icon=$ICON_DIR/spackle.png|" \
    "$DESKTOP_SRC" > "$APP_DIR/spackle.desktop"

# ── Verify PATH ──────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "NOTE: $BIN_DIR is not in your PATH."
    echo "  Add it by appending this line to your ~/.bashrc or ~/.profile:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "==> Done! Spackle has been installed."
echo "    Run it from the terminal:  spackle"
echo "    Or find \"Spackle\" in your application launcher."
