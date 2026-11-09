#!/usr/bin/env bash
# ==============================================================================
# Ubuntu Top Bar Timer - Universal Installer Script
# Supports:
#   - User installation (default, no sudo needed)
#   - System-wide installation (--system, requires sudo)
#   - Debian package building (--deb)
#   - Uninstallation (--uninstall)
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
APP_NAME="timer"
DISPLAY_NAME="Timer"

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}${BOLD}====================================================${NC}"
    echo -e "${BLUE}${BOLD}      ⏱  Ubuntu Top Bar Timer - Installer           ${NC}"
    echo -e "${BLUE}${BOLD}====================================================${NC}"
}

check_dependencies() {
    echo -e "\n${BOLD}Checking system prerequisites...${NC}"
    local missing=0

    # Python3
    if command -v python3 >/dev/null 2>&1; then
        echo -e "  [${GREEN}✔${NC}] Python 3: $(python3 --version)"
    else
        echo -e "  [${RED}✘${NC}] Python 3 is missing. Install with: sudo apt install python3"
        missing=1
    fi

    # Python GTK & DBus
    if python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; import dbus" >/dev/null 2>&1; then
        echo -e "  [${GREEN}✔${NC}] GTK3 & DBus Python bindings available"
    else
        echo -e "  [${YELLOW}!${NC}] Python GTK3/DBus might need: sudo apt install python3-gi python3-dbus gir1.2-gtk-3.0"
    fi

    # notify-send
    if command -v notify-send >/dev/null 2>&1; then
        echo -e "  [${GREEN}✔${NC}] Desktop Notifications (notify-send) available"
    else
        echo -e "  [${YELLOW}!${NC}] Optional: sudo apt install libnotify-bin for notifications"
    fi

    # Audio playback
    if command -v canberra-gtk-play >/dev/null 2>&1 || command -v pw-play >/dev/null 2>&1 || command -v aplay >/dev/null 2>&1; then
        echo -e "  [${GREEN}✔${NC}] Audio alert player available"
    else
        echo -e "  [${YELLOW}!${NC}] Optional: sudo apt install libcanberra-gtk3-module for audio alerts"
    fi

    if [ "$missing" -eq 1 ]; then
        echo -e "\n${RED}Error: Required dependencies are missing. Please install them and rerun.${NC}"
        exit 1
    fi
}

install_user() {
    print_banner
    check_dependencies

    echo -e "\n${BOLD}Installing for current user ($USER)...${NC}"

    TARGET_LIB="$HOME/.local/lib/$APP_NAME"
    TARGET_BIN="$HOME/.local/bin"
    TARGET_APPS="$HOME/.local/share/applications"
    TARGET_ICONS="$HOME/.local/share/icons/hicolor/scalable/apps"

    mkdir -p "$TARGET_LIB" "$TARGET_BIN" "$TARGET_APPS" "$TARGET_ICONS"

    # 1. Copy application files to ~/.local/lib/topbar-timer
    echo "  → Copying application files to $TARGET_LIB..."
    rm -rf "$TARGET_LIB/timer_app" "$TARGET_LIB/assets"
    cp -r "$DIR/timer_app" "$TARGET_LIB/"
    cp -r "$DIR/assets" "$TARGET_LIB/"
    cp "$DIR/run.py" "$TARGET_LIB/run.py"
    chmod +x "$TARGET_LIB/run.py"

    # 2. Create launcher commands in ~/.local/bin
    echo "  → Creating CLI command symlinks in $TARGET_BIN..."
    rm -f "$TARGET_BIN/$APP_NAME" "$TARGET_BIN/topbar-timer" "$TARGET_BIN/timer-app"
    cat << EOF > "$TARGET_BIN/$APP_NAME"
#!/usr/bin/env bash
exec /usr/bin/python3 "$TARGET_LIB/run.py" "\$@"
EOF
    chmod +x "$TARGET_BIN/$APP_NAME"
    ln -sf "$APP_NAME" "$TARGET_BIN/topbar-timer"
    ln -sf "$APP_NAME" "$TARGET_BIN/timer-app"

    # 3. Install icons
    echo "  → Installing application icons..."
    cp "$DIR/assets/timer.svg" "$TARGET_ICONS/timer.svg"
    cp "$DIR/assets/timer-symbolic.svg" "$TARGET_ICONS/timer-symbolic.svg"
    cp "$DIR/assets/timer.svg" "$TARGET_ICONS/ubuntu-topbar-timer.svg"

    # 4. Install desktop entry
    echo "  → Installing desktop launcher..."
    cat << EOF > "$TARGET_APPS/timer.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=$DISPLAY_NAME
GenericName=Countdown Timer & Pomodoro
Comment=Top bar countdown timer showing Hour:minutes:seconds
Exec=$TARGET_BIN/$APP_NAME
Icon=$TARGET_ICONS/timer.svg
Terminal=false
Categories=Utility;Clock;
Keywords=timer;countdown;alarm;pomodoro;clock;
StartupNotify=true
X-GNOME-UsesNotifications=true
EOF
    chmod +x "$TARGET_APPS/timer.desktop"
    ln -sf timer.desktop "$TARGET_APPS/ubuntu-topbar-timer.desktop"

    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$TARGET_APPS" >/dev/null 2>&1 || true
    fi

    # 5. Check PATH for ~/.local/bin
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo -e "  [${YELLOW}!${NC}] Note: Ensure $HOME/.local/bin is in your PATH."
    fi

    echo -e "\n${GREEN}${BOLD}✔ Installation Complete! 🎉${NC}"
    echo -e "You can launch the app by:"
    echo -e "  1. Searching for ${BOLD}'$DISPLAY_NAME'${NC} in Ubuntu Applications (Super / Win key)"
    echo -e "  2. Running ${BOLD}'topbar-timer'${NC} in any terminal"
    echo -e "  3. Quick countdown: ${BOLD}'topbar-timer 25m'${NC} or ${BOLD}'topbar-timer 10s'${NC}"
    echo -e "${BLUE}====================================================${NC}"
}

install_system() {
    print_banner
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Error: System-wide installation requires root privileges.${NC}"
        echo "Please run: sudo ./install.sh --system"
        exit 1
    fi

    check_dependencies
    echo -e "\n${BOLD}Installing system-wide (/usr/lib/$APP_NAME)...${NC}"

    TARGET_LIB="/usr/lib/$APP_NAME"
    TARGET_BIN="/usr/bin"
    TARGET_APPS="/usr/share/applications"
    TARGET_ICONS="/usr/share/icons/hicolor/scalable/apps"

    mkdir -p "$TARGET_LIB" "$TARGET_BIN" "$TARGET_APPS" "$TARGET_ICONS"

    cp -r "$DIR/timer_app" "$TARGET_LIB/"
    cp -r "$DIR/assets" "$TARGET_LIB/"
    cp "$DIR/run.py" "$TARGET_LIB/run.py"
    chmod +x "$TARGET_LIB/run.py"

    cat << EOF > "$TARGET_BIN/$APP_NAME"
#!/usr/bin/env bash
exec /usr/bin/python3 "$TARGET_LIB/run.py" "\$@"
EOF
    chmod +x "$TARGET_BIN/$APP_NAME"
    ln -sf "$APP_NAME" "$TARGET_BIN/timer-app"

    cp "$DIR/assets/timer.svg" "$TARGET_ICONS/ubuntu-topbar-timer.svg"
    cp "$DIR/assets/timer-symbolic.svg" "$TARGET_ICONS/ubuntu-topbar-timer-symbolic.svg"

    cat << EOF > "$TARGET_APPS/ubuntu-topbar-timer.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=$DISPLAY_NAME
GenericName=Countdown Timer
Comment=Ubuntu top bar countdown timer showing Hour:minutes:seconds
Exec=/usr/bin/$APP_NAME
Icon=ubuntu-topbar-timer
Terminal=false
Categories=Utility;Clock;
Keywords=timer;countdown;alarm;pomodoro;clock;
StartupNotify=true
X-GNOME-UsesNotifications=true
EOF

    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$TARGET_APPS" >/dev/null 2>&1 || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
    fi

    echo -e "\n${GREEN}${BOLD}✔ System-wide Installation Complete! 🎉${NC}"
}

do_uninstall() {
    print_banner
    echo -e "\n${BOLD}Uninstalling $DISPLAY_NAME...${NC}"

    # Remove user files
    rm -rf "$HOME/.local/lib/$APP_NAME"
    rm -f "$HOME/.local/bin/$APP_NAME"
    rm -f "$HOME/.local/bin/timer-app"
    rm -f "$HOME/.local/share/applications/ubuntu-topbar-timer.desktop"
    rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/ubuntu-topbar-timer.svg"
    rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/ubuntu-topbar-timer-symbolic.svg"
    rm -f "$HOME/.config/autostart/ubuntu-topbar-timer.desktop"

    if [ "$EUID" -eq 0 ]; then
        rm -rf "/usr/lib/$APP_NAME"
        rm -f "/usr/bin/$APP_NAME"
        rm -f "/usr/bin/timer-app"
        rm -f "/usr/share/applications/ubuntu-topbar-timer.desktop"
        rm -f "/usr/share/icons/hicolor/scalable/apps/ubuntu-topbar-timer.svg"
        rm -f "/usr/share/icons/hicolor/scalable/apps/ubuntu-topbar-timer-symbolic.svg"
    fi

    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
    fi

    echo -e "${GREEN}✔ Successfully uninstalled $DISPLAY_NAME.${NC}"
}

# Command Line Option Parsing
case "$1" in
    --system)
        install_system
        ;;
    --deb)
        "$DIR/build_deb.sh"
        ;;
    --uninstall)
        do_uninstall
        ;;
    --help|-h)
        print_banner
        echo "Usage: ./install.sh [OPTION]"
        echo ""
        echo "Options:"
        echo "  (no args)    Install for current user (recommended, no sudo needed)"
        echo "  --system     Install system-wide for all users (requires sudo)"
        echo "  --deb        Build Debian package (.deb) for Ubuntu"
        echo "  --uninstall  Remove all installed files and shortcuts"
        echo "  --help       Show this help dialog"
        ;;
    *)
        install_user
        ;;
esac
