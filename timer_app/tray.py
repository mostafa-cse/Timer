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
                icon_path = str(ctrl.assets_dir / "timer.png")
                self.icon = pystray.Icon("timer", Image.open(icon_path), "Timer: 00:25:00")
                self.icon.menu = pystray.Menu(
                    pystray.MenuItem("Open Timer", self.controller.show_window),
                    pystray.MenuItem("Toggle", self.controller.on_action_toggle),
                    pystray.MenuItem("Reset", self.controller.on_action_reset),
                    pystray.MenuItem("Quit", self.controller.quit_app)
                )

            def register(self):
                self.icon.run_detached()

            def update_label(self, formatted_time):
                self.icon.title = f"Timer: {formatted_time}"

        tray = PystrayTray(controller)
        tray.register()
        return tray
    except Exception as e:
        print(f"[Tray] Pystray fallback not available: {e}")

    return BaseTray(controller)
