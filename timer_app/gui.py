"""
GTK3 Modern Control Center Window for Ubuntu Top Bar Timer.
Follows GNOME / Ubuntu Yaru Human Interface Guidelines.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango, GLib
from timer_app.core import TimerState


class TimerWindow(Gtk.Window):
    def __init__(self, controller):
        super().__init__(title="Timer")
        self.controller = controller
        self.engine = controller.engine
        self.config = controller.config

        self.set_default_size(440, 480)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("alarm-symbolic")

        # Intercept window close to minimize to top bar
        self.connect("delete-event", self._on_delete_event)

        self._build_ui()
        self._update_display(self.engine.remaining_seconds, self.engine.get_formatted_time(), 0.0)
        self._update_state_ui(self.engine.state)

    def _build_ui(self):
        # HeaderBar
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title("Timer")
        header.set_subtitle("Countdown & Pomodoro")
        self.set_titlebar(header)

        # Minimize to panel button in header
        btn_minimize = Gtk.Button()
        icon_min = Gtk.Image.new_from_icon_name("window-minimize-symbolic", Gtk.IconSize.BUTTON)
        btn_minimize.set_image(icon_min)
        btn_minimize.set_tooltip_text("Hide to Top Bar (Timer keeps running)")
        btn_minimize.connect("clicked", lambda b: self.hide())
        header.pack_end(btn_minimize)

        # Main layout container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        self.add(main_box)

        # 1. Digital Display Section
        display_frame = Gtk.Frame()
        display_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        display_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        display_box.set_margin_top(16)
        display_box.set_margin_bottom(16)
        display_box.set_margin_start(16)
        display_box.set_margin_end(16)

        # Clock Label
        self.lbl_clock = Gtk.Label()
        self.lbl_clock.set_markup("<span font_desc='Monospace 40' weight='bold'>00:25:00</span>")
        self.lbl_clock.set_selectable(False)
        display_box.pack_start(self.lbl_clock, False, False, 0)

        # Status Badge
        self.lbl_status = Gtk.Label()
        self.lbl_status.set_markup("<span size='small' foreground='#5E2750'>⚪ Ready in Top Bar</span>")
        display_box.pack_start(self.lbl_status, False, False, 0)

        # Progress Bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_show_text(False)
        display_box.pack_start(self.progress_bar, False, False, 6)

        display_frame.add(display_box)
        main_box.pack_start(display_frame, False, False, 0)

        # 2. Main Action Buttons (Start / Pause / Reset / Add)
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_homogeneous(True)

        self.btn_toggle = Gtk.Button(label="▶  Start")
        self.btn_toggle.get_style_context().add_class("suggested-action")
        self.btn_toggle.connect("clicked", lambda b: self.controller.on_action_toggle())
        action_box.pack_start(self.btn_toggle, True, True, 0)

        self.btn_reset = Gtk.Button(label="⏹  Reset")
        self.btn_reset.connect("clicked", lambda b: self.controller.on_action_reset())
        action_box.pack_start(self.btn_reset, True, True, 0)

        main_box.pack_start(action_box, False, False, 0)

        # Quick Add Buttons
        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        add_box.set_homogeneous(True)
        for label, secs in [("+1 min", 60), ("+5 min", 300), ("+10 min", 600)]:
            btn_add = Gtk.Button(label=label)
            btn_add.connect("clicked", lambda b, s=secs: self.engine.add_seconds(s))
            add_box.pack_start(btn_add, True, True, 0)
        main_box.pack_start(add_box, False, False, 0)

        # 3. Presets Section
        presets_label = Gtk.Label()
        presets_label.set_markup("<b>Quick Presets</b>")
        presets_label.set_xalign(0.0)
        main_box.pack_start(presets_label, False, False, 0)

        presets_grid = Gtk.Grid()
        presets_grid.set_column_spacing(8)
        presets_grid.set_row_spacing(8)
        presets_grid.set_column_homogeneous(True)

        presets_data = [
            ("☕ 5 min", 300, 0, 0),
            ("🍵 10 min", 600, 1, 0),
            ("⚡ 15 min", 900, 2, 0),
            ("🍅 25 min", 1500, 3, 0),
            ("📚 30 min", 1800, 0, 1),
            ("🎯 45 min", 2700, 1, 1),
            ("⏱ 1 hour", 3600, 2, 1),
            ("⏱ 2 hours", 7200, 3, 1),
        ]
        for name, secs, col, row in presets_data:
            btn = Gtk.Button(label=name)
            btn.connect("clicked", lambda b, s=secs: self._select_preset(s))
            presets_grid.attach(btn, col, row, 1, 1)

        main_box.pack_start(presets_grid, False, False, 0)

        # 4. Custom Time Configuration (Hours : Minutes : Seconds)
        custom_expander = Gtk.Expander(label="Set Custom Time & Task Name")
        custom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        custom_box.set_margin_top(8)

        # Time Spinners
        spin_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        spin_box.set_halign(Gtk.Align.CENTER)

        self.spin_hours = Gtk.SpinButton.new_with_range(0, 99, 1)
        self.spin_mins = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.spin_secs = Gtk.SpinButton.new_with_range(0, 59, 1)

        # Set default to match engine
        h = self.engine.initial_duration // 3600
        m = (self.engine.initial_duration % 3600) // 60
        s = self.engine.initial_duration % 60
        self.spin_hours.set_value(h)
        self.spin_mins.set_value(m)
        self.spin_secs.set_value(s)

        spin_box.pack_start(Gtk.Label(label="H:"), False, False, 0)
        spin_box.pack_start(self.spin_hours, False, False, 0)
        spin_box.pack_start(Gtk.Label(label="M:"), False, False, 0)
        spin_box.pack_start(self.spin_mins, False, False, 0)
        spin_box.pack_start(Gtk.Label(label="S:"), False, False, 0)
        spin_box.pack_start(self.spin_secs, False, False, 0)

        btn_apply = Gtk.Button(label="Apply Time")
        btn_apply.connect("clicked", self._on_apply_custom_time)
        spin_box.pack_start(btn_apply, False, False, 6)

        custom_box.pack_start(spin_box, False, False, 0)

        # Task Name Entry
        task_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        task_box.pack_start(Gtk.Label(label="Task Label:"), False, False, 0)
        self.entry_task = Gtk.Entry()
        self.entry_task.set_placeholder_text("e.g. Pomodoro, Deep Work, Coffee")
        self.entry_task.connect("changed", lambda e: self.engine.set_task_name(e.get_text()))
        task_box.pack_start(self.entry_task, True, True, 0)
        custom_box.pack_start(task_box, False, False, 0)

        custom_expander.add(custom_box)
        main_box.pack_start(custom_expander, False, False, 0)

        # 5. Options Footer
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.chk_sound = Gtk.CheckButton(label="Play Sound on Finish")
        self.chk_sound.set_active(self.config.get("sound_enabled", True))
        self.chk_sound.connect("toggled", lambda b: self.controller.set_sound(b.get_active()))
        options_box.pack_start(self.chk_sound, False, False, 0)

        self.chk_autostart = Gtk.CheckButton(label="Start on Ubuntu Login")
        self.chk_autostart.set_active(self.controller.is_autostart_enabled())
        self.chk_autostart.connect("toggled", lambda b: self.controller.set_autostart(b.get_active()))
        options_box.pack_start(self.chk_autostart, False, False, 0)

        main_box.pack_start(options_box, False, False, 0)

        # Footnote
        footnote = Gtk.Label()
        footnote.set_markup("<span size='x-small' foreground='#777777'>Tip: Closing this window keeps the timer running in the top bar.</span>")
        footnote.set_xalign(0.5)
        main_box.pack_start(footnote, False, False, 0)

    def _select_preset(self, seconds):
        self.engine.set_duration(seconds, auto_start=True)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        self.spin_hours.set_value(h)
        self.spin_mins.set_value(m)
        self.spin_secs.set_value(s)

    def _on_apply_custom_time(self, button):
        h = int(self.spin_hours.get_value())
        m = int(self.spin_mins.get_value())
        s = int(self.spin_secs.get_value())
        total = h * 3600 + m * 60 + s
        if total > 0:
            self.engine.set_duration(total, auto_start=False)

    def _on_delete_event(self, widget, event):
        # Hide instead of closing application
        self.hide()
        return True

    def on_tick(self, remaining_seconds, formatted_time, progress_ratio):
        self._update_display(remaining_seconds, formatted_time, progress_ratio)

    def on_state_changed(self, old_state, new_state):
        self._update_state_ui(new_state)

    def on_finished(self, initial_duration, task_name):
        self._update_state_ui(TimerState.FINISHED)

    def _update_display(self, remaining_seconds, formatted_time, progress_ratio):
        self.lbl_clock.set_markup(f"<span font_desc='Monospace 40' weight='bold'>{formatted_time}</span>")
        self.progress_bar.set_fraction(progress_ratio)

    def _update_state_ui(self, state):
        ctx = self.btn_toggle.get_style_context()
        ctx.remove_class("suggested-action")
        ctx.remove_class("destructive-action")

        if state == TimerState.RUNNING:
            self.btn_toggle.set_label("⏸  Pause")
            self.lbl_status.set_markup("<span size='small' foreground='#26A269' weight='bold'>🟢 Running in Top Bar</span>")
        elif state == TimerState.PAUSED:
            self.btn_toggle.set_label("▶  Resume")
            self.btn_toggle.get_style_context().add_class("suggested-action")
            self.lbl_status.set_markup("<span size='small' foreground='#E95420' weight='bold'>⏸ Paused in Top Bar</span>")
        elif state == TimerState.FINISHED:
            self.btn_toggle.set_label("▶  Restart")
            self.btn_toggle.get_style_context().add_class("suggested-action")
            self.lbl_status.set_markup("<span size='small' foreground='#C01C28' weight='bold'>🔔 Finished! Check notifications</span>")
        else:
            self.btn_toggle.set_label("▶  Start")
            self.btn_toggle.get_style_context().add_class("suggested-action")
            self.lbl_status.set_markup("<span size='small' foreground='#5E2750'>⚪ Ready in Top Bar</span>")
