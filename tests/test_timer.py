"""
Unit and Integration Tests for Timer App.
Tests all topbar dropdown functionalities, TimerEngine, StatusNotifierItem, and GUI sync.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup DBus main loop for tests
try:
    import gi
    gi.require_version('Gtk', '3.0')
    import dbus
    import dbus.service
    import dbus.mainloop.glib
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
except Exception:
    pass

from timer_app.core import TimerEngine, TimerState
from timer_app.config import Config


class DummyController:
    """Mock controller simulating TimerApp for testing TimerDBusMenu."""
    def __init__(self, initial_duration=1500):
        self.assets_dir = PROJECT_ROOT / "assets"
        self.config = {"sound_enabled": True}
        self.engine = TimerEngine(initial_duration=initial_duration)
        self._autostart = False
        self.window_shown = False
        self.quit_called = False

    def is_autostart_enabled(self):
        return self._autostart

    def toggle_autostart(self):
        self._autostart = not self._autostart

    def toggle_sound(self):
        cur = self.config.get("sound_enabled", True)
        self.config["sound_enabled"] = not cur

    def on_action_toggle(self):
        self.engine.toggle()

    def on_action_reset(self):
        self.engine.reset()

    def show_window(self):
        self.window_shown = True

    def toggle_window(self):
        self.window_shown = not self.window_shown

    def quit_app(self):
        self.quit_called = True


class TestTimerEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TimerEngine(initial_duration=1500)

    def test_time_parsing(self):
        self.assertEqual(TimerEngine.parse_time_string("25m"), 1500)
        self.assertEqual(TimerEngine.parse_time_string("1h"), 3600)
        self.assertEqual(TimerEngine.parse_time_string("45s"), 45)
        self.assertEqual(TimerEngine.parse_time_string("1h30m"), 5400)
        self.assertEqual(TimerEngine.parse_time_string("01:15:30"), 4530)
        self.assertEqual(TimerEngine.parse_time_string("25:00"), 1500)
        self.assertEqual(TimerEngine.parse_time_string("300"), 300)

    def test_start_pause_resume_reset(self):
        self.assertEqual(self.engine.state, TimerState.IDLE)
        self.engine.start()
        self.assertEqual(self.engine.state, TimerState.RUNNING)
        self.engine.pause()
        self.assertEqual(self.engine.state, TimerState.PAUSED)
        self.engine.resume()
        self.assertEqual(self.engine.state, TimerState.RUNNING)
        self.engine.reset()
        self.assertEqual(self.engine.state, TimerState.IDLE)
        self.assertEqual(self.engine.remaining_seconds, 1500)

    def test_set_duration_state_notification(self):
        notified_states = []
        notified_durations = []

        class Listener:
            def on_state_changed(self, old, new):
                notified_states.append((old, new))
            def on_duration_changed(self, d):
                notified_durations.append(d)

        self.engine.add_listener(Listener())
        self.engine.state = TimerState.FINISHED

        # Changing duration from FINISHED should notify state change to IDLE
        self.engine.set_duration(600, auto_start=False)
        self.assertEqual(self.engine.state, TimerState.IDLE)
        self.assertEqual(self.engine.remaining_seconds, 600)
        self.assertIn((TimerState.FINISHED, TimerState.IDLE), notified_states)
        self.assertIn(600, notified_durations)

    def test_add_seconds_while_running(self):
        self.engine.set_duration(60, auto_start=True)
        initial = self.engine.remaining_seconds
        self.engine.add_seconds(120)
        # Should have added 120 seconds
        self.assertEqual(self.engine.remaining_seconds, initial + 120)
        self.assertEqual(self.engine.initial_duration, 180)
        self.engine.reset()

    def test_add_seconds_when_finished(self):
        self.engine.state = TimerState.FINISHED
        self.engine.remaining_seconds = 0
        self.engine.initial_duration = 1500

        # Adding 300s (+5m) to a finished timer should set to 300s and start!
        self.engine.add_seconds(300)
        self.assertEqual(self.engine.remaining_seconds, 300)
        self.assertEqual(self.engine.initial_duration, 300)
        self.assertEqual(self.engine.state, TimerState.RUNNING)
        self.engine.reset()


class TestTimerDBusMenu(unittest.TestCase):
    def setUp(self):
        self.ctrl = DummyController(initial_duration=1500)
        bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(f"org.test.TimerMenu.m{abs(id(self))}", bus)
        from timer_app.sni import TimerDBusMenu
        self.menu = TimerDBusMenu(bus_name, f"/TestMenu_m{abs(id(self))}", self.ctrl)

    def test_menu_structure(self):
        rev, layout = self.menu.GetLayout(0, -1, [])
        self.assertEqual(layout[0], 0)  # root ID
        children = layout[2]
        # Should have header, actions, add-time buttons, presets, settings, quit, separators
        self.assertGreater(len(children), 10)

        # Check direct buttons exist
        ids = [c[0] for c in children]
        self.assertIn(1, ids)   # Header
        self.assertIn(3, ids)   # Action toggle
        self.assertIn(4, ids)   # Reset
        self.assertIn(51, ids)  # Add 1m
        self.assertIn(52, ids)  # Add 5m
        self.assertIn(61, ids)  # 5m preset
        self.assertIn(63, ids)  # 25m preset
        self.assertIn(71, ids)  # Sound toggle
        self.assertIn(72, ids)  # Autostart toggle
        self.assertIn(81, ids)  # Open Window
        self.assertIn(11, ids)  # Quit

    def test_get_layout_parent_id(self):
        rev, layout = self.menu.GetLayout(0, -1, [])
        self.assertEqual(layout[0], 0)
        self.assertGreater(len(layout[2]), 10)

    def test_action_toggle_and_state_label(self):
        # 1. Initially IDLE -> label is "▶ Start Timer"
        self.assertEqual(self.ctrl.engine.state, TimerState.IDLE)
        prop = self.menu.GetProperty(3, "label")
        self.assertIn("Start", str(prop))

        # 2. Click Start (item 3)
        self.menu.Event(3, "clicked", 0, 0)
        self.assertEqual(self.ctrl.engine.state, TimerState.RUNNING)
        prop = self.menu.GetProperty(3, "label")
        self.assertIn("Pause", str(prop))

        # 3. Click Pause (item 3)
        self.menu.Event(3, "clicked", 0, 0)
        self.assertEqual(self.ctrl.engine.state, TimerState.PAUSED)
        prop = self.menu.GetProperty(3, "label")
        self.assertIn("Resume", str(prop))

        # 4. Click Reset (item 4)
        self.menu.Event(4, "clicked", 0, 0)
        self.assertEqual(self.ctrl.engine.state, TimerState.IDLE)
        prop = self.menu.GetProperty(3, "label")
        self.assertIn("Start", str(prop))

    def test_add_time_functionality(self):
        self.ctrl.engine.set_duration(300, auto_start=True)
        # Click +5 Minutes (item 52)
        self.menu.Event(52, "clicked", 0, 0)
        self.assertGreaterEqual(self.ctrl.engine.remaining_seconds, 595)
        self.ctrl.engine.reset()

    def test_quick_presets_functionality(self):
        # Preset 61: 5 Minutes (300s)
        self.menu.Event(61, "clicked", 0, 0)
        self.assertEqual(self.ctrl.engine.initial_duration, 300)
        self.assertEqual(self.ctrl.engine.state, TimerState.RUNNING)

        # Preset 63: 25 Minutes (1500s)
        self.menu.Event(63, "clicked", 0, 0)
        self.assertEqual(self.ctrl.engine.initial_duration, 1500)
        self.assertEqual(self.ctrl.engine.state, TimerState.RUNNING)
        self.ctrl.engine.reset()

    def test_settings_toggle_functionality(self):
        # Sound toggle (item 71)
        self.assertTrue(self.ctrl.config["sound_enabled"])
        self.menu.Event(71, "clicked", 0, 0)
        self.assertFalse(self.ctrl.config["sound_enabled"])
        state = self.menu.GetProperty(71, "toggle-state")
        self.assertEqual(int(state), 0)

        # Autostart toggle (item 72)
        self.assertFalse(self.ctrl.is_autostart_enabled())
        self.menu.Event(72, "clicked", 0, 0)
        self.assertTrue(self.ctrl.is_autostart_enabled())
        state = self.menu.GetProperty(72, "toggle-state")
        self.assertEqual(int(state), 1)

    def test_open_window_and_quit(self):
        self.assertFalse(self.ctrl.window_shown)
        self.menu.Event(81, "clicked", 0, 0)
        self.assertTrue(self.ctrl.window_shown)

        self.assertFalse(self.ctrl.quit_called)
        self.menu.Event(11, "clicked", 0, 0)
        self.assertTrue(self.ctrl.quit_called)

    def test_about_to_show_updates_properties(self):
        # Changing engine state directly
        self.ctrl.engine.set_duration(1800, auto_start=True)
        # AboutToShow should rebuild and emit property updates, returning False so GNOME Shell doesn't collapse submenus
        self.assertFalse(self.menu.AboutToShow(0))
        prop = self.menu.GetProperty(1, "label")
        self.assertIn("Running", str(prop))
        self.assertIn("00:30:00", str(prop))
        self.ctrl.engine.reset()

    def test_update_tick_label(self):
        self.ctrl.engine.start()
        self.menu.update_tick_label("00:24:45")
        prop = self.menu.GetProperty(1, "label")
        self.assertIn("00:24:45", str(prop))
        self.ctrl.engine.reset()


class TestStatusNotifierItem(unittest.TestCase):
    def setUp(self):
        self.ctrl = DummyController(initial_duration=1500)
        bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(f"org.test.SNI.m{abs(id(self))}", bus)
        from timer_app.sni import StatusNotifierTimerItem
        self.sni = StatusNotifierTimerItem(bus, self.ctrl, bus_name=bus_name, path=f"/SNI_m{abs(id(self))}")

    def test_sni_properties(self):
        props = self.sni.GetAll("org.kde.StatusNotifierItem")
        self.assertEqual(str(props["Category"]), "ApplicationStatus")
        self.assertEqual(str(props["Id"]), "ubuntu-topbar-timer")
        self.assertEqual(str(props["Status"]), "Active")
        self.assertEqual(str(props["IconName"]), "alarm-symbolic")
        self.assertEqual(str(props["XAyatanaLabelGuide"]), "00:00:00")
        self.assertEqual(str(props["Menu"]), "/MenuBar")

    def test_scroll_direction(self):
        # In GNOME Clutter: delta < 0 is scroll UP (increase time)
        self.ctrl.engine.set_duration(300, auto_start=False)
        self.sni.Scroll(-1, "vertical")
        self.assertEqual(self.ctrl.engine.remaining_seconds, 360)

        # delta > 0 is scroll DOWN (decrease time)
        self.sni.Scroll(1, "vertical")
        self.assertEqual(self.ctrl.engine.remaining_seconds, 300)

    def test_control_methods(self):
        self.sni.SetDuration(900, True)
        self.assertEqual(self.ctrl.engine.remaining_seconds, 900)
        self.assertEqual(self.ctrl.engine.state, TimerState.RUNNING)

        self.sni.Toggle()
        self.assertEqual(self.ctrl.engine.state, TimerState.PAUSED)

        self.sni.Reset()
        self.assertEqual(self.ctrl.engine.state, TimerState.IDLE)


class TestTimerWindow(unittest.TestCase):
    def setUp(self):
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        from timer_app.gui import TimerWindow
        self.ctrl = DummyController(initial_duration=1500)
        self.ctrl.config = Config()
        self.win = TimerWindow(self.ctrl)

    def test_window_duration_sync(self):
        # When duration changes in engine (e.g. from topbar preset), spinners must update
        self.win.on_duration_changed(3725)  # 1h 2m 5s
        self.assertEqual(int(self.win.spin_hours.get_value()), 1)
        self.assertEqual(int(self.win.spin_mins.get_value()), 2)
        self.assertEqual(int(self.win.spin_secs.get_value()), 5)

    def test_window_state_ui(self):
        self.win.on_state_changed(TimerState.IDLE, TimerState.RUNNING)
        self.assertEqual(self.win.btn_toggle.get_label(), "⏸  Pause")

        self.win.on_state_changed(TimerState.RUNNING, TimerState.PAUSED)
        self.assertEqual(self.win.btn_toggle.get_label(), "▶  Resume")

        self.win.on_state_changed(TimerState.PAUSED, TimerState.FINISHED)
        self.assertEqual(self.win.btn_toggle.get_label(), "▶  Restart")

        self.win.on_state_changed(TimerState.FINISHED, TimerState.IDLE)
        self.assertEqual(self.win.btn_toggle.get_label(), "▶  Start")

    def tearDown(self):
        self.win.destroy()


if __name__ == "__main__":
    unittest.main()
