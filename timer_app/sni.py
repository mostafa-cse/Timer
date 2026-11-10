"""
StatusNotifierItem (SNI) and DBusMenu implementation for Ubuntu Top Bar.
Presents a live 'HH:MM:SS' label directly in Ubuntu's top panel.
"""

import os
import dbus
import dbus.service
from timer_app.core import TimerState


class DBusMenuItem:
    def __init__(self, item_id, label="", item_type="standard", enabled=True, visible=True, callback=None, toggle_type=None, toggle_state=0):
        self.item_id = item_id
        self.label = label
        self.item_type = item_type
        self.enabled = enabled
        self.visible = visible
        self.callback = callback
        self.toggle_type = toggle_type
        self.toggle_state = toggle_state
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

        if self.toggle_type:
            d["toggle-type"] = dbus.String(self.toggle_type)
            d["toggle-state"] = dbus.Int32(1 if self.toggle_state else 0)

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
        # Pre-populate items map immediately
        self._build_menu_tree()

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
        sound_label = f"🔔 Sound Alert ({'ON' if sound_enabled else 'OFF'})"

        autostart_active = self.controller.is_autostart_enabled()
        autostart_label = f"🚀 Start on Login ({'ON' if autostart_active else 'OFF'})"

        root = DBusMenuItem(0)

        # 1. Header / Status
        root.add_child(DBusMenuItem(1, label=status_text, enabled=False))
        root.add_child(DBusMenuItem(2, item_type="separator"))

        # 2. Main control action (Start / Pause / Resume / Restart)
        root.add_child(DBusMenuItem(3, label=action_label, callback=self.controller.on_action_toggle))
        root.add_child(DBusMenuItem(4, label="⏹ Reset Timer", callback=self.controller.on_action_reset))
        root.add_child(DBusMenuItem(5, item_type="separator"))

        # 3. Direct Add Time (Immediate 1-click response, no unresponsive submenus)
        root.add_child(DBusMenuItem(51, label="➕ Add 1 Minute", callback=lambda: engine.add_seconds(60)))
        root.add_child(DBusMenuItem(52, label="➕ Add 5 Minutes", callback=lambda: engine.add_seconds(300)))
        root.add_child(DBusMenuItem(53, label="➕ Add 10 Minutes", callback=lambda: engine.add_seconds(600)))
        root.add_child(DBusMenuItem(6, item_type="separator"))

        # 4. Direct Quick Presets (Immediate 1-click launch)
        presets = [
            (61, "☕ 5 Min (Break)", 300),
            (62, "⚡ 15 Minutes", 900),
            (63, "🍅 25 Min (Pomodoro)", 1500),
            (64, "🎯 45 Min (Deep Work)", 2700),
            (65, "⏱ 1 Hour", 3600),
        ]
        for p_id, p_label, p_secs in presets:
            root.add_child(DBusMenuItem(p_id, label=p_label, callback=lambda s=p_secs: engine.set_duration(s, auto_start=True)))
        root.add_child(DBusMenuItem(7, item_type="separator"))

        # 5. Direct Settings (Immediate 1-click toggles)
        root.add_child(DBusMenuItem(71, label=sound_label, toggle_type="checkmark", toggle_state=1 if sound_enabled else 0, callback=self.controller.toggle_sound))
        root.add_child(DBusMenuItem(72, label=autostart_label, toggle_type="checkmark", toggle_state=1 if autostart_active else 0, callback=self.controller.toggle_autostart))
        root.add_child(DBusMenuItem(8, item_type="separator"))

        # 6. Open Control Center GUI
        root.add_child(DBusMenuItem(81, label="🎛 Open Timer Window...", callback=self.controller.show_window))
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

    def _emit_properties_updated(self):
        """Notify DBusMenu clients (e.g. GNOME Shell) that item properties changed."""
        updated = []
        for item_id, item in self._items_map.items():
            updated.append(dbus.Struct(
                (dbus.Int32(item_id), item.to_dbus_dict()),
                signature="ia{sv}"
            ))
        self.ItemsPropertiesUpdated(
            dbus.Array(updated, signature="(ia{sv})"),
            dbus.Array([], signature="(ias)")
        )

    def refresh_menu(self):
        self.revision += 1
        self._build_menu_tree()
        self.LayoutUpdated(self.revision, 0)
        self._emit_properties_updated()

    def update_tick_label(self, formatted_time):
        """Update live countdown in dropdown menu during ticks."""
        if 1 in self._items_map:
            item = self._items_map[1]
            engine = self.controller.engine
            task_info = f" ({engine.task_name})" if engine.task_name else ""
            if engine.state == TimerState.RUNNING:
                item.label = f"⏱ Running: {formatted_time}{task_info}"
            elif engine.state == TimerState.PAUSED:
                item.label = f"⏸ Paused: {formatted_time}{task_info}"
            elif engine.state == TimerState.FINISHED:
                item.label = f"⏰ Finished! (00:00:00){task_info}"
            else:
                item.label = f"⏱ Timer: {formatted_time} [Ready]{task_info}"

            updated = [dbus.Struct((dbus.Int32(1), item.to_dbus_dict()), signature="ia{sv}")]
            self.ItemsPropertiesUpdated(
                dbus.Array(updated, signature="(ia{sv})"),
                dbus.Array([], signature="(ias)")
            )

    @dbus.service.method("com.canonical.dbusmenu", in_signature="iias", out_signature="u(ia{sv}av)")
    def GetLayout(self, parent_id, recursion_depth, property_names):
        root = self._build_menu_tree()
        parent_id = int(parent_id)
        if parent_id == 0 or parent_id not in self._items_map:
            target_item = root
        else:
            target_item = self._items_map[parent_id]
        return dbus.UInt32(self.revision), target_item.to_layout_struct()

    @dbus.service.method("com.canonical.dbusmenu", in_signature="aias", out_signature="a(ia{sv})")
    def GetGroupProperties(self, ids, property_names):
        if not self._items_map:
            self._build_menu_tree()
        res = []
        for i in ids:
            item = self._items_map.get(int(i))
            if item:
                res.append(dbus.Struct((dbus.Int32(int(i)), item.to_dbus_dict()), signature="ia{sv}"))
        return res

    @dbus.service.method("com.canonical.dbusmenu", in_signature="is", out_signature="v")
    def GetProperty(self, item_id, name):
        if not self._items_map:
            self._build_menu_tree()
        item = self._items_map.get(int(item_id))
        if item:
            d = item.to_dbus_dict()
            if name in d:
                return d[name]
        return ""

    @dbus.service.method("com.canonical.dbusmenu", in_signature="isvu", out_signature="")
    def Event(self, item_id, event_id, data, timestamp):
        item_id = int(item_id)
        if not self._items_map:
            self._build_menu_tree()
        if event_id == "clicked":
            item = self._items_map.get(item_id)
            if item and item.callback:
                try:
                    item.callback()
                except Exception as e:
                    print(f"[TopBarTimer] Error in menu callback for item {item_id}: {e}")
                self.refresh_menu()

    @dbus.service.method("com.canonical.dbusmenu", in_signature="a(isvu)", out_signature="ai")
    def EventGroup(self, events):
        errors = []
        for e in events:
            try:
                self.Event(e[0], e[1], e[2], e[3])
            except Exception:
                errors.append(e[0])
        return errors

    @dbus.service.method("com.canonical.dbusmenu", in_signature="i", out_signature="b")
    def AboutToShow(self, item_id):
        self._build_menu_tree()
        self._emit_properties_updated()
        # Return False to indicate the submenu layout structure has not changed.
        # Returning True causes GNOME Shell to reload the layout and collapse the submenu!
        return dbus.Boolean(False)

    @dbus.service.method("com.canonical.dbusmenu", in_signature="ai", out_signature="aiai")
    def AboutToShowGroup(self, ids):
        self._build_menu_tree()
        self._emit_properties_updated()
        # First list: IDs needing layout updates (none).
        # Second list: IDs not needing layout updates (all requested).
        return ([], list(ids))

    @dbus.service.signal("com.canonical.dbusmenu", signature="ui")
    def LayoutUpdated(self, revision, parent):
        pass

    @dbus.service.signal("com.canonical.dbusmenu", signature="a(ia{sv})a(ias)")
    def ItemsPropertiesUpdated(self, updated_props, removed_props):
        pass


class StatusNotifierTimerItem(dbus.service.Object):
    def __init__(self, bus, controller, bus_name=None, path="/StatusNotifierItem"):
        self.bus = bus
        self.controller = controller
        self.engine = controller.engine
        self.path = path

        if bus_name is None:
            self.bus_name = dbus.service.BusName("org.kde.StatusNotifierItem-ubuntu-topbar-timer", bus)
        else:
            self.bus_name = bus_name
        super().__init__(self.bus_name, path)

        menu_path = "/MenuBar" if path == "/StatusNotifierItem" else f"{path}_MenuBar"
        self.menu = TimerDBusMenu(self.bus_name, menu_path, controller)
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
                dbus.Dictionary({
                    "XAyatanaLabel": dbus.String(new_label),
                    "Title": dbus.String(f"Timer ({new_label})")
                }, signature="sv"),
                dbus.Array([], signature="s")
            )

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="ss", out_signature="v")
    def Get(self, interface, prop):
        return self.GetAll(interface).get(prop, "")

    @dbus.service.method("com.ubuntu.TopBarTimer", in_signature="ib", out_signature="")
    def SetDuration(self, seconds, auto_start):
        self.engine.set_duration(seconds, auto_start=auto_start)
        self.menu.refresh_menu()

    @dbus.service.method("com.ubuntu.TopBarTimer", in_signature="i", out_signature="")
    def AddSeconds(self, seconds):
        self.engine.add_seconds(seconds)
        self.menu.refresh_menu()

    @dbus.service.method("com.ubuntu.TopBarTimer", in_signature="", out_signature="")
    def Toggle(self):
        self.controller.on_action_toggle()
        self.menu.refresh_menu()

    @dbus.service.method("com.ubuntu.TopBarTimer", in_signature="", out_signature="")
    def Reset(self):
        self.controller.on_action_reset()
        self.menu.refresh_menu()

    @dbus.service.method("com.ubuntu.TopBarTimer", in_signature="", out_signature="")
    def ShowGUI(self):
        self.controller.show_window()

    @dbus.service.method("org.freedesktop.DBus.Properties", in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface == "org.kde.StatusNotifierItem":
            assets_path = str(self.controller.assets_dir)
            return {
                "Category": dbus.String("ApplicationStatus"),
                "Id": dbus.String("ubuntu-topbar-timer"),
                "Title": dbus.String(f"Timer ({self.current_label})"),
                "Status": dbus.String("Active"),
                "IconName": dbus.String("alarm-symbolic"),
                "IconThemePath": dbus.String(assets_path),
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
        self.menu.refresh_menu()

    @dbus.service.method("org.kde.StatusNotifierItem", in_signature="ii", out_signature="")
    def SecondaryActivate(self, x, y):
        # Middle click / secondary click: toggle Start / Pause
        self.controller.on_action_toggle()
        self.menu.refresh_menu()

    @dbus.service.method("org.kde.StatusNotifierItem", in_signature="is", out_signature="")
    def Scroll(self, delta, orientation):
        # In GNOME smooth scrolling: scroll UP is delta < 0, scroll DOWN is delta > 0
        if delta < 0:
            self.engine.add_seconds(60)
        else:
            self.engine.add_seconds(-60)
        self.menu.refresh_menu()

    @dbus.service.signal("org.kde.StatusNotifierItem", signature="ss")
    def XAyatanaNewLabel(self, label, guide):
        pass

    @dbus.service.signal("org.freedesktop.DBus.Properties", signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed, invalidated):
        pass
