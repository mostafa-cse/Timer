#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "========================================================"
echo "        Building Timer for macOS (Timer.app)            "
echo "========================================================"

# Install dependencies
python3 -m pip install --upgrade pip
pip3 install pyinstaller pillow pyobjc-framework-Cocoa

# Build .app bundle
pyinstaller --windowed --name "Timer" --icon "$DIR/assets/timer.png" --add-data "$DIR/assets:assets" "$DIR/run.py"

cd "$DIR/dist"
zip -r "$DIR/Timer-macos.zip" Timer.app

echo ""
echo "========================================================"
echo "Build Successful: $DIR/Timer-macos.zip"
echo "========================================================"
