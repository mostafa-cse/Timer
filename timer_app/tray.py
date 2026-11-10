"""
Cross-platform Tray and Top Bar abstraction for Timer.
- Linux: Embedded Ubuntu GNOME Top Panel (Ayatana StatusNotifierItem with live 'HH:MM:SS' text)
- macOS: Embedded macOS Menu Bar (NSStatusBar statusItem with live 'HH:MM:SS' text)
- Windows: System Tray Icon with live tooltip & notifications
"""

import sys
from timer_app.core import TimerState


class BaseTray:
    def __init__(self, controller):
        self.controller = controller
        self.engine = controller.engine

    def register(self):
        pass

    def update_label(self, formatted_time):
        pass

    def refresh_menu(self):
        pass


def create_tray(controller):
    platform = sys.platform

    # 1. Linux: Ubuntu GNOME Top Panel
    if platform.startswith("linux"):
        try:
            from timer_app.sni import StatusNotifierTimerItem
            import dbus
            bus = dbus.SessionBus()
            item = StatusNotifierTimerItem(bus, controller)
            item.register()
            return item
        except Exception as e:
            print(f"[Tray] Failed to initialize Linux SNI: {e}")

    # 2. macOS: Top Menu Bar (NSStatusBar)
    elif platform == "darwin":
        try:
            from AppKit import NSStatusBar, NSVariableStatusItemLength, NSMenu, NSMenuItem
            class MacOSTray(BaseTray):
                def __init__(self, ctrl):
                    super().__init__(ctrl)
                    self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
                    self.button = self.status_item.button()
                    self.update_label(self.engine.get_formatted_time())

                def update_label(self, formatted_time):
                    if self.button:
                        self.button.setTitle_(formatted_time)

            return MacOSTray(controller)
        except Exception as e:
            print(f"[Tray] macOS native status bar not available: {e}")

    # 3. Windows & Universal Fallback: pystray
    try:
        import pystray
        from PIL import Image

        class PystrayTray(BaseTray):
            def __init__(self, ctrl):
                super().__init__(ctrl)
                self.ctrl = ctrl
                icon_path = str(ctrl.assets_dir / "timer.png")
                self.icon = pystray.Icon("timer", Image.open(icon_path), "Timer: 00:25:00")
                self._update_menu()

            def _update_menu(self):
                engine = self.ctrl.engine
                state = engine.state
                if state == TimerState.RUNNING:
                    action_label = "⏸ Pause Timer"
                elif state == TimerState.PAUSED:
                    action_label = "▶ Resume Timer"
                elif state == TimerState.FINISHED:
                    action_label = "▶ Restart Timer"
                else:
                    action_label = "▶ Start Timer"

                sound_enabled = self.controller.config.get("sound_enabled", True)
                sound_label = f"Sound Alert ({'ON' if sound_enabled else 'OFF'})"
                autostart_active = self.controller.is_autostart_enabled()
                autostart_label = f"Start on Login ({'ON' if autostart_active else 'OFF'})"

                self.icon.menu = pystray.Menu(
                    pystray.MenuItem("🎛 Open Control Center", self.controller.show_window),
                    pystray.MenuItem(action_label, self.controller.on_action_toggle),
                    pystray.MenuItem("⏹ Reset Timer", self.controller.on_action_reset),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("+ Add Time", pystray.Menu(
                        pystray.MenuItem("+ 1 Minute", lambda: engine.add_seconds(60)),
                        pystray.MenuItem("+ 5 Minutes", lambda: engine.add_seconds(300)),
                        pystray.MenuItem("+ 10 Minutes", lambda: engine.add_seconds(600)),
                        pystray.MenuItem("+ 15 Minutes", lambda: engine.add_seconds(900)),
                    )),
                    pystray.MenuItem("⚡ Quick Presets", pystray.Menu(
                        pystray.MenuItem("5 Min (Break)", lambda: engine.set_duration(300, auto_start=True)),
                        pystray.MenuItem("15 Min (Session)", lambda: engine.set_duration(900, auto_start=True)),
                        pystray.MenuItem("25 Min (Pomodoro)", lambda: engine.set_duration(1500, auto_start=True)),
                        pystray.MenuItem("45 Min (Deep Work)", lambda: engine.set_duration(2700, auto_start=True)),
                        pystray.MenuItem("1 Hour (Focus)", lambda: engine.set_duration(3600, auto_start=True)),
                        pystray.MenuItem("2 Hours (Extended)", lambda: engine.set_duration(7200, auto_start=True)),
                    )),
                    pystray.MenuItem("⚙ Settings", pystray.Menu(
                        pystray.MenuItem(sound_label, self.controller.toggle_sound),
                        pystray.MenuItem(autostart_label, self.controller.toggle_autostart),
                    )),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Quit Timer", self.controller.quit_app)
                )

            def register(self):
                self.icon.run_detached()

            def update_label(self, formatted_time):
                self.icon.title = f"Timer: {formatted_time}"

            def refresh_menu(self):
                self._update_menu()

        tray = PystrayTray(controller)
        tray.register()
        return tray
    except Exception as e:
        print(f"[Tray] Pystray fallback not available: {e}")

    return BaseTray(controller)
