#!/usr/bin/env python3
"""
Timer - Cross-platform Countdown Timer & Pomodoro for Linux, macOS, and Windows.
Usage:
    timer                  # Open Timer with GUI
    timer --minimized      # Start in Top Bar / System Tray only (no window)
    timer 25m              # Start 25-minute countdown immediately
    timer 01:30:00         # Start 1h 30m countdown
    timer +5m              # Add 5 minutes to active timer
    timer --toggle         # Toggle running timer (pause/resume)
    timer --reset          # Reset running timer
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup DBus on Linux
if sys.platform.startswith("linux"):
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        import dbus
        import dbus.mainloop.glib
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    except Exception:
        pass

from timer_app.core import TimerEngine
from timer_app.app import TimerApp

BUS_NAME = "org.kde.StatusNotifierItem-ubuntu-topbar-timer"
OBJ_PATH = "/StatusNotifierItem"


def is_already_running(bus):
    try:
        return bus.name_has_owner(BUS_NAME)
    except Exception:
        return False


def send_to_running_instance(bus, action, extra_arg=None):
    try:
        obj = bus.get_object(BUS_NAME, OBJ_PATH)
        if action == "activate":
            try:
                obj.ShowGUI(dbus_interface="com.ubuntu.TopBarTimer")
            except Exception:
                obj.Activate(0, 0, dbus_interface="org.kde.StatusNotifierItem")
            print("[Timer] Activated existing Timer window.")
            return True
        elif action == "toggle":
            try:
                obj.Toggle(dbus_interface="com.ubuntu.TopBarTimer")
            except Exception:
                obj.SecondaryActivate(0, 0, dbus_interface="org.kde.StatusNotifierItem")
            print("[Timer] Toggled running timer.")
            return True
        elif action == "reset":
            try:
                obj.Reset(dbus_interface="com.ubuntu.TopBarTimer")
            except Exception:
                menu_obj = bus.get_object(BUS_NAME, "/MenuBar")
                menu_obj.Event(4, "clicked", 0, 0, dbus_interface="com.canonical.dbusmenu")
            print("[Timer] Reset running timer.")
            return True
        elif action == "set_duration":
            obj.SetDuration(extra_arg, True, dbus_interface="com.ubuntu.TopBarTimer")
            print(f"[Timer] Updated running timer to {extra_arg} seconds and started.")
            return True
        elif action == "add_seconds":
            obj.AddSeconds(extra_arg, dbus_interface="com.ubuntu.TopBarTimer")
            print(f"[Timer] Added {extra_arg} seconds to running timer.")
            return True
    except Exception as e:
        print(f"[Timer] Error communicating with running instance: {e}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Timer - High Efficiency Countdown Timer for Linux, macOS & Windows")
    parser.add_argument("time", nargs="?", help="Optional duration to set/start (e.g., 25m, 1h, 00:15:00, 30s, +5m)")
    parser.add_argument("-m", "--minimized", action="store_true", help="Start directly in top bar/tray without opening window")
    parser.add_argument("-t", "--toggle", action="store_true", help="Toggle start/pause on running timer")
    parser.add_argument("-r", "--reset", action="store_true", help="Reset running timer")
    parser.add_argument("--gui", action="store_true", help="Bring timer window to front")

    args = parser.parse_args()

    # Check DBus on Linux for existing instance
    if sys.platform.startswith("linux"):
        try:
            import dbus
            bus = dbus.SessionBus()
            running = is_already_running(bus)
        except Exception:
            bus = None
            running = False

        if running:
            if args.toggle:
                send_to_running_instance(bus, "toggle")
                return
            elif args.reset:
                send_to_running_instance(bus, "reset")
                return
            elif args.time:
                time_str = args.time.strip()
                if time_str.startswith("+"):
                    parsed = TimerEngine.parse_time_string(time_str[1:])
                    if parsed:
                        send_to_running_instance(bus, "add_seconds", parsed)
                        return
                parsed = TimerEngine.parse_time_string(time_str)
                if parsed:
                    send_to_running_instance(bus, "set_duration", parsed)
                    return
            # Default action when already running is to bring window to front
            send_to_running_instance(bus, "activate")
            return

    # Parse duration if provided
    duration_secs = None
    auto_start = False
    if args.time:
        parsed = TimerEngine.parse_time_string(args.time)
        if parsed:
            duration_secs = parsed
            auto_start = True
            print(f"[Timer] Setting countdown to {parsed} seconds ({args.time}).")
        else:
            print(f"[Timer] Warning: Could not parse time string '{args.time}'. Using default.")

    show_gui = not args.minimized
    app = TimerApp(show_gui=show_gui, start_duration=duration_secs, auto_start_timer=auto_start)
    app.run()


if __name__ == "__main__":
    main()
