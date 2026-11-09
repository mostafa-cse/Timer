#!/usr/bin/env bash
set -e

echo "Uninstalling Ubuntu Top Bar Timer..."

rm -f "$HOME/.local/bin/timer-app"
rm -f "$HOME/.local/bin/topbar-timer"
rm -f "$HOME/.local/share/applications/ubuntu-topbar-timer.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/ubuntu-topbar-timer.svg"
rm -f "$HOME/.config/autostart/ubuntu-topbar-timer.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

echo "✔ Successfully uninstalled Ubuntu Top Bar Timer."
