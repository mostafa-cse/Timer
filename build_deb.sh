#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BUILD_ROOT="$DIR/build/deb_package"
PACKAGE_NAME="timer"
VERSION="1.0.0"
DEB_FILENAME="${PACKAGE_NAME}_${VERSION}_all.deb"

echo "=========================================================="
echo "   Building Ubuntu Debian Package: $DEB_FILENAME"
echo "=========================================================="

rm -rf "$BUILD_ROOT"
mkdir -p "$BUILD_ROOT/DEBIAN"
mkdir -p "$BUILD_ROOT/usr/bin"
mkdir -p "$BUILD_ROOT/usr/lib/$PACKAGE_NAME"
mkdir -p "$BUILD_ROOT/usr/share/applications"
mkdir -p "$BUILD_ROOT/usr/share/icons/hicolor/scalable/apps"

# 1. DEBIAN/control
cat << 'EOF' > "$BUILD_ROOT/DEBIAN/control"
Package: timer
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-3.0, python3-dbus, libnotify-bin
Maintainer: Timer Project <m0stafa@ubuntu.com>
Description: High-efficiency top bar countdown timer for Linux, macOS & Windows
 A cross-platform countdown timer that shows live time in
 Hour:minutes:seconds (HH:MM:SS) format on the top panel,
 with rich desktop notifications and audio alert on completion.
EOF

# 2. DEBIAN/postinst
cat << 'EOF' > "$BUILD_ROOT/DEBIAN/postinst"
#!/bin/sh
set -e
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
exit 0
EOF
chmod 755 "$BUILD_ROOT/DEBIAN/postinst"

# 3. DEBIAN/prerm
cat << 'EOF' > "$BUILD_ROOT/DEBIAN/prerm"
#!/bin/sh
set -e
pkill -f "/usr/lib/timer/run.py" >/dev/null 2>&1 || true
exit 0
EOF
chmod 755 "$BUILD_ROOT/DEBIAN/prerm"

# 4. Copy application source files to /usr/lib/timer/
cp -r "$DIR/timer_app" "$BUILD_ROOT/usr/lib/$PACKAGE_NAME/"
cp -r "$DIR/assets" "$BUILD_ROOT/usr/lib/$PACKAGE_NAME/"
cp "$DIR/run.py" "$BUILD_ROOT/usr/lib/$PACKAGE_NAME/run.py"
chmod +x "$BUILD_ROOT/usr/lib/$PACKAGE_NAME/run.py"

# Clean any __pycache__ in package
find "$BUILD_ROOT/usr/lib/$PACKAGE_NAME" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 5. Create launcher in /usr/bin/timer and backward-compatible aliases
cat << 'EOF' > "$BUILD_ROOT/usr/bin/timer"
#!/usr/bin/env bash
exec /usr/bin/python3 /usr/lib/timer/run.py "$@"
EOF
chmod 755 "$BUILD_ROOT/usr/bin/timer"

ln -sf timer "$BUILD_ROOT/usr/bin/topbar-timer"
ln -sf timer "$BUILD_ROOT/usr/bin/timer-app"

# 6. Icons
cp "$DIR/assets/timer.svg" "$BUILD_ROOT/usr/share/icons/hicolor/scalable/apps/timer.svg"
cp "$DIR/assets/timer-symbolic.svg" "$BUILD_ROOT/usr/share/icons/hicolor/scalable/apps/timer-symbolic.svg"

# 7. Desktop entry
cat << 'EOF' > "$BUILD_ROOT/usr/share/applications/timer.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Timer
GenericName=Countdown Timer & Pomodoro
Comment=Top bar countdown timer showing Hour:minutes:seconds
Exec=/usr/bin/timer
Icon=timer
Terminal=false
Categories=Utility;Clock;
Keywords=timer;countdown;alarm;pomodoro;clock;
StartupNotify=true
X-GNOME-UsesNotifications=true
EOF

# 8. Build package
dpkg-deb --build --root-owner-group "$BUILD_ROOT" "$DIR/$DEB_FILENAME"

# Also link legacy filename for convenience
ln -sf "$DEB_FILENAME" "$DIR/topbar-timer_1.0.0_all.deb"

echo ""
echo "✔ Successfully generated: $DIR/$DEB_FILENAME"
echo "To install on any Ubuntu system, run:"
echo "    sudo dpkg -i $DIR/$DEB_FILENAME || sudo apt-get install -f"
echo "=========================================================="
