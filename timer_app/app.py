"""
Main application controller for Ubuntu Top Bar Timer.
Wires together DBus SNI, GTK3 UI, Sound, Notifications, and Core Engine.
"""

import os
import sys
from pathlib import Path

from timer_app.config import Config
from timer_app.core import TimerEngine, TimerState
from timer_app.sound import SoundPlayer
from timer_app.notifier import Notifier
from timer_app.tray import create_tray

# Try importing GTK3 on Linux
HAS_GTK = False
if sys.platform.startswith("linux"):
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, GLib
        HAS_GTK = True
    except Exception:
        HAS_GTK = False

if HAS_GTK:
    from timer_app.gui import TimerWindow
else:
    from timer_app.gui_crossplatform import TkTimerWindow as TimerWindow

AUTOSTART_DIR = Path.home() / ".config" / "autostart"
AUTOSTART_FILE = AUTOSTART_DIR / "timer.desktop"


class TimerApp:
    def __init__(self, show_gui=True, start_duration=None, auto_start_timer=False):
        self.assets_dir = Path(__file__).resolve().parent.parent / "assets"
        self.config = Config()
        self.sound_player = SoundPlayer()
        self.notifier = Notifier(on_restart_callback=self.on_action_restart)

        default_secs = self.config.get("default_duration_seconds", 1500)
        if start_duration:
            default_secs = start_duration

        self.engine = TimerEngine(initial_duration=default_secs)
        self.engine.add_listener(self)

        # Initialize Tray / Top Bar
        self.tray = create_tray(self)

        # Initialize GUI Window
        self.window = TimerWindow(self)
        self.engine.add_listener(self.window)

        if show_gui:
            self.show_window()
        else:
            self.window.hide()

        if auto_start_timer:
            self.engine.start()

    def on_tick(self, remaining_seconds, formatted_time, progress_ratio):
        # Update top bar dynamic label with exact Hour:minutes:seconds
        if hasattr(self.tray, "update_label"):
            self.tray.update_label(formatted_time)

    def on_state_changed(self, old_state, new_state):
        if hasattr(self.tray, "menu") and hasattr(self.tray.menu, "refresh_menu"):
            self.tray.menu.refresh_menu()

    def on_finished(self, initial_duration, task_name):
        if hasattr(self.tray, "update_label"):
            self.tray.update_label("00:00:00")
        if hasattr(self.tray, "menu") and hasattr(self.tray.menu, "refresh_menu"):
            self.tray.menu.refresh_menu()

        # Desktop notification
        self.notifier.send_timer_finished(initial_duration, task_name)

        # Sound chime
        if self.config.get("sound_enabled", True):
            repeats = self.config.get("sound_repeats", 2)
            self.sound_player.play_alarm_async(repeats=repeats)

    def on_action_toggle(self):
        self.engine.toggle()

    def on_action_reset(self):
        self.engine.reset()

    def on_action_restart(self):
        self.engine.reset()
        self.engine.start()

    def toggle_window(self):
        if hasattr(self.window, "is_visible") and self.window.is_visible():
            self.window.hide()
        else:
            self.show_window()

    def show_window(self):
        if HAS_GTK:
            self.window.show_all()
            self.window.present()
        else:
            self.window.show()

    def is_autostart_enabled(self):
        return AUTOSTART_FILE.exists()

    def set_autostart(self, enabled):
        try:
            if enabled:
                AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
                desktop_source = Path(__file__).resolve().parent.parent / "timer.desktop"
                if desktop_source.exists():
                    content = desktop_source.read_text(encoding="utf-8")
                else:
                    exec_path = sys.executable + " " + str(Path(__file__).resolve().parent.parent / "run.py") + " --minimized"
                    content = f"""[Desktop Entry]
Type=Application
Name=Timer
Comment=Top Bar Countdown Timer
Exec={exec_path}
Icon=alarm-symbolic
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""
                AUTOSTART_FILE.write_text(content, encoding="utf-8")
            else:
                if AUTOSTART_FILE.exists():
                    AUTOSTART_FILE.unlink()
            if hasattr(self.tray, "menu") and hasattr(self.tray.menu, "refresh_menu"):
                self.tray.menu.refresh_menu()
        except Exception as e:
            print(f"[TimerApp] Autostart error: {e}")

    def toggle_autostart(self):
        self.set_autostart(not self.is_autostart_enabled())

    def toggle_sound(self):
        cur = self.config.get("sound_enabled", True)
        self.set_sound(not cur)

    def set_sound(self, enabled):
        self.config.set("sound_enabled", enabled)
        if hasattr(self.window, "chk_sound"):
            self.window.chk_sound.set_active(enabled)
        if hasattr(self.tray, "menu") and hasattr(self.tray.menu, "refresh_menu"):
            self.tray.menu.refresh_menu()

    def quit_app(self):
        print("[TimerApp] Quitting Timer.")
        if HAS_GTK:
            Gtk.main_quit()
        elif hasattr(self.window, "root"):
            self.window.root.destroy()
        sys.exit(0)

    def run(self):
        if HAS_GTK:
            Gtk.main()
        elif hasattr(self.window, "root"):
            self.window.root.mainloop()
