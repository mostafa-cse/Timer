"""
StatusNotifierItem (SNI) and DBusMenu implementation for Ubuntu Top Bar.
Presents a live 'HH:MM:SS' label directly in Ubuntu's top panel.
"""

import os
import dbus
import dbus.service
from timer_app.core import TimerState


class DBusMenuItem:
    def __init__(self, item_id, label="", item_type="standard", enabled=True, visible=True, callback=None):
        self.item_id = item_id
        self.label = label
        self.item_type = item_type
        self.enabled = enabled
        self.visible = visible
        self.callback = callback
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def to_dbus_dict(self):
        d = {
            "visible": dbus.Boolean(self.visible),
            "enabled": dbus.Boolean(self.enabled)
        }
        if self.item_type == "separator":
            d["type"] = dbus.String("separator")
        else:
            d["label"] = dbus.String(self.label)

        if self.children:
            d["children-display"] = dbus.String("submenu")
        return dbus.Dictionary(d, signature="sv")

    def to_layout_struct(self):
        children_structs = dbus.Array([c.to_layout_struct() for c in self.children], signature="v")
        return dbus.Struct((
            dbus.Int32(self.item_id),
            self.to_dbus_dict(),
            children_structs
        ), signature="ia{sv}av")


class TimerDBusMenu(dbus.service.Object):
    def __init__(self, bus_name, path, controller):
        super().__init__(bus_name, path)
        self.controller = controller
        self.revision = 1
        self._items_map = {}

    def _build_menu_tree(self):
        engine = self.controller.engine
        state = engine.state
        time_str = engine.get_formatted_time()
        task_info = f" ({engine.task_name})" if engine.task_name else ""

        if state == TimerState.RUNNING:
            status_text = f"⏱ Running: {time_str}{task_info}"
            action_label = "⏸ Pause Timer"
        elif state == TimerState.PAUSED:
            status_text = f"⏸ Paused: {time_str}{task_info}"
            action_label = "▶ Resume Timer"
        elif state == TimerState.FINISHED:
            status_text = f"⏰ Finished! (00:00:00){task_info}"
            action_label = "▶ Restart Timer"
        else:
            status_text = f"⏱ Timer: {time_str} [Ready]{task_info}"
            action_label = "▶ Start Timer"

        sound_enabled = self.controller.config.get("sound_enabled", True)
        sound_label = f"🔔 Sound: {'ON' if sound_enabled else 'OFF'}"

        autostart_active = self.controller.is_autostart_enabled()
        autostart_label = f"🚀 Start on Boot: {'ON' if autostart_active else 'OFF'}"

        root = DBusMenuItem(0)

        # 1. Header / Status
        root.add_child(DBusMenuItem(1, label=status_text, enabled=False))
        root.add_child(DBusMenuItem(2, item_type="separator"))

        # 2. Main control action
        root.add_child(DBusMenuItem(3, label=action_label, callback=self.controller.on_action_toggle))
        root.add_child(DBusMenuItem(4, label="⏹ Reset Timer", callback=self.controller.on_action_reset))

        # 3. Add Time Submenu
        add_menu = DBusMenuItem(5, label="➕ Add Time")
        add_menu.add_child(DBusMenuItem(51, label="+1 Minute", callback=lambda: engine.add_seconds(60)))
        add_menu.add_child(DBusMenuItem(52, label="+5 Minutes", callback=lambda: engine.add_seconds(300)))
        add_menu.add_child(DBusMenuItem(53, label="+10 Minutes", callback=lambda: engine.add_seconds(600)))
        add_menu.add_child(DBusMenuItem(54, label="+15 Minutes", callback=lambda: engine.add_seconds(900)))
        root.add_child(add_menu)

        # 4. Presets Submenu
        presets = [
            (61, "☕ 5 Minutes (Quick Break)", 300),
            (62, "🍵 10 Minutes (Coffee Break)", 600),
            (63, "⚡ 15 Minutes", 900),
            (64, "🍅 25 Minutes (Pomodoro)", 1500),
            (65, "📚 30 Minutes", 1800),
            (66, "🎯 45 Minutes (Deep Work)", 2700),
            (67, "⏱ 1 Hour", 3600),
            (68, "⏱ 2 Hours", 7200),
        ]
        pres_menu = DBusMenuItem(6, label="⚡ Quick Presets")
        for p_id, p_label, p_secs in presets:
            pres_menu.add_child(DBusMenuItem(p_id, label=p_label, callback=lambda s=p_secs: engine.set_duration(s, auto_start=True)))
        root.add_child(pres_menu)

        root.add_child(DBusMenuItem(7, item_type="separator"))

        # 5. Open Control Center GUI
        root.add_child(DBusMenuItem(8, label="🎛 Open Timer Window...", callback=self.controller.show_window))

        # 6. Settings Submenu
        settings_menu = DBusMenuItem(9, label="⚙ Settings")
        settings_menu.add_child(DBusMenuItem(91, label=sound_label, callback=self.controller.toggle_sound))
        settings_menu.add_child(DBusMenuItem(92, label=autostart_label, callback=self.controller.toggle_autostart))
        root.add_child(settings_menu)

        root.add_child(DBusMenuItem(10, item_type="separator"))

        # 7. Quit
        root.add_child(DBusMenuItem(11, label="❌ Quit Timer", callback=self.controller.quit_app))

        # Map IDs
        self._items_map = {}
        def map_items(item):
            self._items_map[item.item_id] = item
            for c in item.children:
                map_items(c)
        map_items(root)
        return root

    def refresh_menu(self):
        self.revision += 1
        self.LayoutUpdated(self.revision, 0)

    @dbus.service.method("com.canonical.dbusmenu", in_signature="iias", out_signature="u(ia{sv}av)")
    def GetLayout(self, parent_id, recursion_depth, property_names):
        root = self._build_menu_tree()
        layout_struct = root.to_layout_struct()
        return dbus.UInt32(self.revision), layout_struct

    @dbus.service.method("com.canonical.dbusmenu", in_signature="aias", out_signature="a(ia{sv})")
    def GetGroupProperties(self, ids, property_names):
        res = []
        for i in ids:
            item = self._items_map.get(i)
            if item:
                res.append(dbus.Struct((dbus.Int32(i), item.to_dbus_dict()), signature="ia{sv}"))
        return res

    @dbus.service.method("com.canonical.dbusmenu", in_signature="is", out_signature="v")
    def GetProperty(self, item_id, name):
        item = self._items_map.get(item_id)
        if item:
            d = item.to_dbus_dict()
            return d.get(name, "")
        return ""

    @dbus.service.method("com.canonical.dbusmenu", in_signature="isvu", out_signature="")
    def Event(self, item_id, event_id, data, timestamp):
        if event_id == "clicked":
            item = self._items_map.get(item_id)
            if item and item.callback:
                item.callback()
                self.refresh_menu()

    @dbus.service.method("com.canonical.dbusmenu", in_signature="a(isvu)", out_signature="ai")
    def EventGroup(self, events):
        errors = []
        for e in events:
            self.Event(e[0], e[1], e[2], e[3])
        return errors

    @dbus.service.method("com.canonical.dbusmenu", in_signature="i", out_signature="b")
    def AboutToShow(self, item_id):
        return True

    @dbus.service.method("com.canonical.dbusmenu", in_signature="ai", out_signature="aiai")
    def AboutToShowGroup(self, ids):
        return (list(ids), [])

    @dbus.service.signal("com.canonical.dbusmenu", signature="ui")
    def LayoutUpdated(self, revision, parent):
        pass


class StatusNotifierTimerItem(dbus.service.Object):
    def __init__(self, bus, controller):
        self.bus = bus
        self.controller = controller
        self.engine = controller.engine

        self.bus_name = dbus.service.BusName("org.kde.StatusNotifierItem-ubuntu-topbar-timer", bus)
        super().__init__(self.bus_name, "/StatusNotifierItem")

        self.menu = TimerDBusMenu(self.bus_name, "/MenuBar", controller)
        self.current_label = self.engine.get_formatted_time()

    def register(self):
        try:
            watcher = self.bus.get_object("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher")
            watcher.RegisterStatusNotifierItem("/StatusNotifierItem", dbus_interface="org.kde.StatusNotifierWatcher")
            print("[TopBarTimer] Successfully registered to StatusNotifierWatcher on top bar.")
            return True
        except Exception as e:
            print(f"[TopBarTimer] Registration to StatusNotifierWatcher failed: {e}")
            return False

    def update_label(self, new_label):
        if new_label != self.current_label:
            self.current_label = new_label
            self.XAyatanaNewLabel(new_label, "00:00:00")
            self.PropertiesChanged(
                "org.kde.StatusNotifierItem",
                dbus.Dictionary({"XAyatanaLabel": dbus.String(new_label)}, signature="sv"),
                dbus.Array([], signature="s")
            )

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="ss", out_signature="v")
    def Get(self, interface, prop):
        return self.GetAll(interface).get(prop, "")

    @dbus.service.method("com.ubuntu.TopBarTimer", in_signature="ib", out_signature="")
    def SetDuration(self, seconds, auto_start):
        self.engine.set_duration(seconds, auto_start=auto_start)

    @dbus.service.method("com.ubuntu.TopBarTimer", in_signature="i", out_signature="")
    def AddSeconds(self, seconds):
        self.engine.add_seconds(seconds)

    @dbus.service.method("com.ubuntu.TopBarTimer", in_signature="", out_signature="")
    def Toggle(self):
        self.controller.on_action_toggle()

    @dbus.service.method("com.ubuntu.TopBarTimer", in_signature="", out_signature="")
    def Reset(self):
        self.controller.on_action_reset()

    @dbus.service.method("com.ubuntu.TopBarTimer", in_signature="", out_signature="")
    def ShowGUI(self):
        self.controller.show_window()

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface == "org.kde.StatusNotifierItem":
            return {
                "Category": dbus.String("ApplicationStatus"),
                "Id": dbus.String("ubuntu-topbar-timer"),
                "Title": dbus.String(f"Timer ({self.current_label})"),
                "Status": dbus.String("Active"),
                "IconName": dbus.String("alarm-symbolic"),
                "IconThemePath": dbus.String(""),
                "ItemIsMenu": dbus.Boolean(False),
                "Menu": dbus.ObjectPath("/MenuBar"),
                "XAyatanaLabel": dbus.String(self.current_label),
                "XAyatanaLabelGuide": dbus.String("00:00:00")
            }
        return {}

    @dbus.service.method("org.kde.StatusNotifierItem", in_signature="ii", out_signature="")
    def Activate(self, x, y):
        # Clicked directly on indicator: open / toggle the GUI window
        self.controller.toggle_window()

    @dbus.service.method("org.kde.StatusNotifierItem", in_signature="ii", out_signature="")
    def ContextMenu(self, x, y):
        pass

    @dbus.service.method("org.kde.StatusNotifierItem", in_signature="ii", out_signature="")
    def SecondaryActivate(self, x, y):
        # Middle click / secondary click: toggle Start / Pause
        self.controller.on_action_toggle()

    @dbus.service.method("org.kde.StatusNotifierItem", in_signature="is", out_signature="")
    def Scroll(self, delta, orientation):
        # Mouse wheel on indicator scrolls time +1 min / -1 min
        if delta > 0:
            self.engine.add_seconds(60)
        else:
            self.engine.add_seconds(-60)

    @dbus.service.signal("org.kde.StatusNotifierItem", signature="ss")
    def XAyatanaNewLabel(self, label, guide):
        pass

    @dbus.service.signal("org.freedesktop.DBus.Properties", signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed, invalidated):
        pass
