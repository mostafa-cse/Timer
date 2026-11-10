"""
GTK3 Modern Classic Control Center Window for Ubuntu Top Bar Timer.
Features a classic, high-contrast dark theme combining Ubuntu Warm Orange,
crisp pure white, and deep obsidian slate.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango, GLib
from timer_app.core import TimerState


CUSTOM_CSS = """
/* Ubuntu Warm Orange & Classic Precision Dark Theme */
window, .timer-window {
    background-color: #16161E;
    color: #FFFFFF;
}

headerbar {
    background-color: #1A1B26;
    border-bottom: 1px solid #292E42;
    color: #FFFFFF;
}

headerbar .title {
    font-weight: 700;
    font-size: 13pt;
    color: #FFFFFF;
}

headerbar .subtitle {
    font-size: 9pt;
    color: #A9B1D6;
}

headerbar button {
    background-color: #24283B;
    border: 1px solid #3B4261;
    color: #C0CAF5;
    border-radius: 8px;
    padding: 4px 8px;
}

headerbar button:hover {
    background-color: #2F354F;
    color: #FFFFFF;
    border-color: #E95420;
}

/* Digital Display Card */
.display-card {
    background-color: #1F2335;
    border: 1px solid #292E42;
    border-radius: 16px;
    padding: 16px;
}

.display-screen {
    background-color: #13141F;
    border: 1px solid #24283B;
    border-radius: 12px;
    padding: 14px 20px;
}

.clock-text {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', 'Liberation Mono', monospace;
    font-size: 42pt;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: 2px;
}

.status-badge {
    font-size: 10pt;
    font-weight: 600;
}

/* Progress Bar */
progressbar trough {
    background-color: #13141F;
    border-radius: 6px;
    min-height: 8px;
    border: 1px solid #292E42;
}

progressbar progress {
    background-image: linear-gradient(90deg, #E95420, #FF7800);
    border-radius: 6px;
    min-height: 8px;
}

/* Primary Action Buttons */
.btn-action-start {
    background-image: linear-gradient(135deg, #E95420 0%, #FF6622 100%);
    color: #FFFFFF;
    font-size: 12pt;
    font-weight: 700;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
    box-shadow: 0 4px 14px rgba(233, 84, 32, 0.35);
}

.btn-action-start:hover {
    background-image: linear-gradient(135deg, #FF6622 0%, #FF8533 100%);
    box-shadow: 0 6px 20px rgba(233, 84, 32, 0.5);
    color: #FFFFFF;
}

.btn-action-start:active {
    background-image: linear-gradient(135deg, #CF4410 0%, #E95420 100%);
}

.btn-action-pause {
    background-image: linear-gradient(135deg, #238636 0%, #2EA043 100%);
    color: #FFFFFF;
    font-size: 12pt;
    font-weight: 700;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
    box-shadow: 0 4px 14px rgba(46, 160, 67, 0.35);
}

.btn-action-pause:hover {
    background-image: linear-gradient(135deg, #2EA043 0%, #3FB950 100%);
    box-shadow: 0 6px 20px rgba(46, 160, 67, 0.5);
    color: #FFFFFF;
}

.btn-action-reset {
    background-color: #24283B;
    border: 1px solid #3B4261;
    color: #C0CAF5;
    font-size: 12pt;
    font-weight: 600;
    border-radius: 10px;
    padding: 10px 20px;
}

.btn-action-reset:hover {
    background-color: #2F354F;
    border-color: #FF7800;
    color: #FFFFFF;
}

/* Quick Add Buttons */
.btn-quick-add {
    background-color: #24283B;
    border: 1px solid #3B4261;
    color: #C0CAF5;
    font-weight: 600;
    font-size: 10pt;
    border-radius: 8px;
    padding: 7px 12px;
}

.btn-quick-add:hover {
    background-color: #2F354F;
    border-color: #E95420;
    color: #FF8533;
}

/* Preset Buttons */
.btn-preset {
    background-color: #1F2335;
    border: 1px solid #2E334D;
    color: #C0CAF5;
    font-size: 10pt;
    font-weight: 500;
    border-radius: 8px;
    padding: 8px 10px;
}

.btn-preset:hover {
    background-color: #292E42;
    border-color: #E95420;
    color: #FFFFFF;
}

/* Inputs & Spinbuttons */
spinbutton, entry {
    background-color: #1F2335;
    color: #FFFFFF;
    border: 1px solid #3B4261;
    border-radius: 8px;
    padding: 6px 10px;
}

spinbutton:focus, entry:focus {
    border-color: #E95420;
    box-shadow: 0 0 0 1px #E95420;
}

/* CheckButtons */
checkbutton {
    color: #C0CAF5;
    font-size: 10pt;
}

checkbutton:hover {
    color: #FFFFFF;
}

checkbutton check {
    background-color: #1F2335;
    border: 1px solid #3B4261;
    border-radius: 5px;
    min-width: 16px;
    min-height: 16px;
}

checkbutton check:checked {
    background-color: #E95420;
    border-color: #FF7800;
    color: #FFFFFF;
}

/* Expander */
expander title {
    color: #A9B1D6;
    font-weight: 600;
}

expander title:hover {
    color: #FF8533;
}
"""

_CSS_LOADED = False


def load_application_css():
    global _CSS_LOADED
    if _CSS_LOADED:
        return
    try:
        provider = Gtk.CssProvider()
        provider.load_from_data(CUSTOM_CSS.encode('utf-8'))
        screen = Gdk.Screen.get_default()
        if screen:
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        _CSS_LOADED = True
    except Exception as e:
        print(f"[UI] Warning: Failed to apply CSS provider: {e}")


class TimerWindow(Gtk.Window):
    def __init__(self, controller):
        super().__init__(title="Timer")
        self.controller = controller
        self.engine = controller.engine
        self.config = controller.config

        load_application_css()

        self.set_default_size(440, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("alarm-symbolic")
        self.get_style_context().add_class("timer-window")

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
        header.set_subtitle("Focus & Countdown")
        self.set_titlebar(header)

        # Minimize to panel button in header
        btn_minimize = Gtk.Button()
        icon_min = Gtk.Image.new_from_icon_name("window-minimize-symbolic", Gtk.IconSize.BUTTON)
        btn_minimize.set_image(icon_min)
        btn_minimize.set_tooltip_text("Minimize to Top Bar (Timer keeps running)")
        btn_minimize.connect("clicked", lambda b: self.hide())
        header.pack_end(btn_minimize)

        # Main layout container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        self.add(main_box)

        # 1. Digital Display Section
        card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card_box.get_style_context().add_class("display-card")

        screen_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        screen_box.get_style_context().add_class("display-screen")

        # Clock Label
        self.lbl_clock = Gtk.Label()
        self.lbl_clock.get_style_context().add_class("clock-text")
        self.lbl_clock.set_markup("<span font_desc='Monospace 40' weight='bold' foreground='#FFFFFF'>00:25:00</span>")
        self.lbl_clock.set_selectable(False)
        screen_box.pack_start(self.lbl_clock, False, False, 2)

        # Status Badge
        self.lbl_status = Gtk.Label()
        self.lbl_status.get_style_context().add_class("status-badge")
        self.lbl_status.set_markup("<span size='small' foreground='#A9B1D6'>⚪ Ready in Top Bar</span>")
        screen_box.pack_start(self.lbl_status, False, False, 0)

        card_box.pack_start(screen_box, False, False, 0)

        # Progress Bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_show_text(False)
        card_box.pack_start(self.progress_bar, False, False, 4)

        main_box.pack_start(card_box, False, False, 0)

        # 2. Main Action Buttons (Start / Pause / Reset)
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_homogeneous(True)

        self.btn_toggle = Gtk.Button(label="▶  Start")
        self.btn_toggle.get_style_context().add_class("btn-action-start")
        self.btn_toggle.connect("clicked", lambda b: self.controller.on_action_toggle())
        action_box.pack_start(self.btn_toggle, True, True, 0)

        self.btn_reset = Gtk.Button(label="⏹  Reset")
        self.btn_reset.get_style_context().add_class("btn-action-reset")
        self.btn_reset.connect("clicked", lambda b: self.controller.on_action_reset())
        action_box.pack_start(self.btn_reset, True, True, 0)

        main_box.pack_start(action_box, False, False, 0)

        # 3. Quick Add Buttons (+1m, +5m, +10m)
        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        add_box.set_homogeneous(True)
        for label, secs in [("+1 min", 60), ("+5 min", 300), ("+10 min", 600)]:
            btn_add = Gtk.Button(label=label)
            btn_add.get_style_context().add_class("btn-quick-add")
            btn_add.connect("clicked", lambda b, s=secs: self.engine.add_seconds(s))
            add_box.pack_start(btn_add, True, True, 0)
        main_box.pack_start(add_box, False, False, 0)

        # 4. Presets Section
        presets_label = Gtk.Label()
        presets_label.set_markup("<span weight='bold' foreground='#FFFFFF'>⚡ Quick Presets</span>")
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
            ("⏳ 2 hours", 7200, 3, 1),
        ]
        for name, secs, col, row in presets_data:
            btn = Gtk.Button(label=name)
            btn.get_style_context().add_class("btn-preset")
            btn.connect("clicked", lambda b, s=secs: self._select_preset(s))
            presets_grid.attach(btn, col, row, 1, 1)

        main_box.pack_start(presets_grid, False, False, 0)

        # 5. Custom Time Configuration (Hours : Minutes : Seconds)
        custom_expander = Gtk.Expander(label="Custom Duration & Task Label")
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

        lbl_h = Gtk.Label(label="H:")
        lbl_h.get_style_context().add_class("text-muted")
        spin_box.pack_start(lbl_h, False, False, 0)
        spin_box.pack_start(self.spin_hours, False, False, 0)

        lbl_m = Gtk.Label(label="M:")
        spin_box.pack_start(lbl_m, False, False, 0)
        spin_box.pack_start(self.spin_mins, False, False, 0)

        lbl_s = Gtk.Label(label="S:")
        spin_box.pack_start(lbl_s, False, False, 0)
        spin_box.pack_start(self.spin_secs, False, False, 0)

        btn_apply = Gtk.Button(label="Apply Time")
        btn_apply.get_style_context().add_class("btn-quick-add")
        btn_apply.connect("clicked", self._on_apply_custom_time)
        spin_box.pack_start(btn_apply, False, False, 6)

        custom_box.pack_start(spin_box, False, False, 0)

        # Task Name Entry
        task_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl_task = Gtk.Label(label="Task Label:")
        task_box.pack_start(lbl_task, False, False, 0)
        self.entry_task = Gtk.Entry()
        self.entry_task.set_placeholder_text("e.g. Pomodoro, Deep Work, Reading")
        self.entry_task.connect("changed", lambda e: self.engine.set_task_name(e.get_text()))
        task_box.pack_start(self.entry_task, True, True, 0)
        custom_box.pack_start(task_box, False, False, 0)

        custom_expander.add(custom_box)
        main_box.pack_start(custom_expander, False, False, 0)

        # 6. Options Footer
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.chk_sound = Gtk.CheckButton(label="Play Sound on Finish")
        self.chk_sound.set_active(self.config.get("sound_enabled", True))
        self.chk_sound.connect("toggled", lambda b: self._on_chk_sound_toggled(b))
        options_box.pack_start(self.chk_sound, False, False, 0)

        self.chk_autostart = Gtk.CheckButton(label="Start on Ubuntu Login")
        self.chk_autostart.set_active(self.controller.is_autostart_enabled())
        self.chk_autostart.connect("toggled", lambda b: self._on_chk_autostart_toggled(b))
        options_box.pack_start(self.chk_autostart, False, False, 0)

        main_box.pack_start(options_box, False, False, 0)

        # Footnote
        footnote = Gtk.Label()
        footnote.set_markup("<span size='small' foreground='#7AA2F7'>💡 Tip:</span> <span size='small' foreground='#A9B1D6'>Minimizing or closing keeps the timer running in your Ubuntu top panel.</span>")
        footnote.set_xalign(0.5)
        main_box.pack_start(footnote, False, False, 0)

    def _on_chk_sound_toggled(self, button):
        val = button.get_active()
        if self.config.get("sound_enabled", True) != val:
            self.controller.set_sound(val)

    def _on_chk_autostart_toggled(self, button):
        val = button.get_active()
        if self.controller.is_autostart_enabled() != val:
            self.controller.set_autostart(val)

    def _select_preset(self, seconds):
        self.engine.set_duration(seconds, auto_start=True)

    def on_duration_changed(self, seconds):
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
        self.lbl_clock.set_markup(f"<span font_desc='Monospace 40' weight='bold' foreground='#FFFFFF'>{formatted_time}</span>")
        self.progress_bar.set_fraction(progress_ratio)

    def _update_state_ui(self, state):
        ctx = self.btn_toggle.get_style_context()
        ctx.remove_class("btn-action-start")
        ctx.remove_class("btn-action-pause")

        if state == TimerState.RUNNING:
            self.btn_toggle.set_label("⏸  Pause")
            ctx.add_class("btn-action-pause")
            self.lbl_status.set_markup("<span size='small' foreground='#3FB950' weight='bold'>● RUNNING</span> <span size='small' foreground='#A9B1D6'>in Top Bar</span>")
        elif state == TimerState.PAUSED:
            self.btn_toggle.set_label("▶  Resume")
            ctx.add_class("btn-action-start")
            self.lbl_status.set_markup("<span size='small' foreground='#FF8533' weight='bold'>❚❚ PAUSED</span> <span size='small' foreground='#A9B1D6'>in Top Bar</span>")
        elif state == TimerState.FINISHED:
            self.btn_toggle.set_label("▶  Restart")
            ctx.add_class("btn-action-start")
            self.lbl_status.set_markup("<span size='small' foreground='#F7768E' weight='bold'>🔔 TIME'S UP!</span> <span size='small' foreground='#A9B1D6'>Check Notification</span>")
        else:
            self.btn_toggle.set_label("▶  Start")
            ctx.add_class("btn-action-start")
            self.lbl_status.set_markup("<span size='small' foreground='#A9B1D6' weight='bold'>○ READY</span> <span size='small' foreground='#7AA2F7'>Top Bar Active</span>")
