"""
Universal Cross-Platform GUI Window for Timer (Windows, macOS, fallback).
Built using Python's standard Tkinter with a classic dark theme combining
Ubuntu Warm Orange (#E95420), crisp pure white (#FFFFFF), and deep obsidian slate (#16161E).
"""

import sys
from timer_app.core import TimerState

try:
    import tkinter as tk
    from tkinter import ttk
    HAS_TK = True
except ImportError:
    HAS_TK = False


class TkTimerWindow:
    def __init__(self, controller):
        if not HAS_TK:
            raise RuntimeError("Tkinter is not installed on this system.")

        self.controller = controller
        self.engine = controller.engine
        self.config = controller.config

        self.root = tk.Tk()
        self.root.title("Timer")
        self.root.geometry("420x510")
        self.root.resizable(False, False)
        self.root.configure(bg="#16161E")

        # Handle window close (minimize instead of quit)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

        self._build_ui()
        self._update_display(self.engine.get_formatted_time(), 0.0)
        self._update_state_ui(self.engine.state)

    def _build_ui(self):
        # 1. Header Frame
        header = tk.Frame(self.root, bg="#1A1B26", height=45)
        header.pack(fill=tk.X, side=tk.TOP)
        lbl_title = tk.Label(header, text="Timer", font=("Helvetica", 14, "bold"), fg="#FFFFFF", bg="#1A1B26")
        lbl_title.pack(side=tk.LEFT, padx=16, pady=10)

        btn_min = tk.Button(header, text="—", font=("Helvetica", 11, "bold"), fg="#C0CAF5", bg="#24283B",
                            activebackground="#2F354F", activeforeground="#FFFFFF",
                            relief=tk.FLAT, bd=0, padx=8, pady=2, command=self.hide)
        btn_min.pack(side=tk.RIGHT, padx=14, pady=10)

        # 2. Main Container
        main = tk.Frame(self.root, bg="#16161E")
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        # Display Card
        card = tk.Frame(main, bg="#1F2335", bd=1, relief=tk.SOLID)
        card.pack(fill=tk.X, pady=(0, 14), ipadx=10, ipady=12)

        # Inner Screen Well
        screen = tk.Frame(card, bg="#13141F", bd=1, relief=tk.SOLID)
        screen.pack(fill=tk.X, padx=10, pady=6, ipadx=6, ipady=10)

        # Digital Clock
        self.lbl_clock = tk.Label(screen, text="00:25:00", font=("Courier", 38, "bold"),
                                  fg="#FFFFFF", bg="#13141F")
        self.lbl_clock.pack(pady=(4, 2))

        self.lbl_status = tk.Label(screen, text="○ READY", font=("Helvetica", 10, "bold"),
                                   fg="#A9B1D6", bg="#13141F")
        self.lbl_status.pack(pady=(0, 4))

        # Action Buttons (Start / Pause / Reset)
        btn_frame = tk.Frame(main, bg="#16161E")
        btn_frame.pack(fill=tk.X, pady=6)

        self.btn_toggle = tk.Button(btn_frame, text="▶ Start", font=("Helvetica", 12, "bold"),
                                    bg="#E95420", fg="#FFFFFF", activebackground="#FF6622",
                                    activeforeground="#FFFFFF", relief=tk.FLAT, bd=0, padx=16, pady=8,
                                    command=self.controller.on_action_toggle)
        self.btn_toggle.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

        self.btn_reset = tk.Button(btn_frame, text="⏹ Reset", font=("Helvetica", 12, "bold"),
                                   bg="#24283B", fg="#C0CAF5", activebackground="#2F354F",
                                   activeforeground="#FFFFFF", relief=tk.FLAT, bd=0, padx=16, pady=8,
                                   command=self.controller.on_action_reset)
        self.btn_reset.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

        # Quick Adjustments (+1m, +5m, +10m)
        adj_frame = tk.Frame(main, bg="#16161E")
        adj_frame.pack(fill=tk.X, pady=6)
        for text, secs in [("+1m", 60), ("+5m", 300), ("+10m", 600)]:
            b = tk.Button(adj_frame, text=text, font=("Helvetica", 10, "bold"),
                          bg="#24283B", fg="#C0CAF5", activebackground="#2F354F",
                          activeforeground="#FF8533", relief=tk.FLAT, bd=0, pady=6,
                          command=lambda s=secs: self.engine.add_seconds(s))
            b.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        # Presets Section
        lbl_presets = tk.Label(main, text="⚡ Quick Presets", font=("Helvetica", 11, "bold"),
                               fg="#FFFFFF", bg="#16161E", anchor="w")
        lbl_presets.pack(fill=tk.X, pady=(10, 6))

        pres_grid = tk.Frame(main, bg="#16161E")
        pres_grid.pack(fill=tk.X)

        presets = [
            ("☕ 5m", 300), ("🍵 10m", 600), ("⚡ 15m", 900), ("🍅 25m", 1500),
            ("📚 30m", 1800), ("🎯 45m", 2700), ("⏱ 1h", 3600), ("⏳ 2h", 7200)
        ]
        for idx, (label, secs) in enumerate(presets):
            row = idx // 4
            col = idx % 4
            b = tk.Button(pres_grid, text=label, font=("Helvetica", 9),
                          bg="#1F2335", fg="#C0CAF5", activebackground="#292E42",
                          activeforeground="#FFFFFF", relief=tk.FLAT, bd=0, pady=6,
                          command=lambda s=secs: self._select_preset(s))
            b.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            pres_grid.grid_columnconfigure(col, weight=1)

        # Custom Time Frame
        custom_frame = tk.Frame(main, bg="#16161E")
        custom_frame.pack(fill=tk.X, pady=(14, 6))

        lbl_custom = tk.Label(custom_frame, text="Set H:M:S:", font=("Helvetica", 10),
                              fg="#A9B1D6", bg="#16161E")
        lbl_custom.pack(side=tk.LEFT, padx=4)

        self.spin_h = tk.Spinbox(custom_frame, from_=0, to=99, width=3, font=("Helvetica", 11),
                                 bg="#1F2335", fg="#FFFFFF", insertbackground="#FFFFFF", bd=1)
        self.spin_h.pack(side=tk.LEFT, padx=2)
        self.spin_m = tk.Spinbox(custom_frame, from_=0, to=59, width=3, font=("Helvetica", 11),
                                 bg="#1F2335", fg="#FFFFFF", insertbackground="#FFFFFF", bd=1)
        self.spin_m.pack(side=tk.LEFT, padx=2)
        self.spin_s = tk.Spinbox(custom_frame, from_=0, to=59, width=3, font=("Helvetica", 11),
                                 bg="#1F2335", fg="#FFFFFF", insertbackground="#FFFFFF", bd=1)
        self.spin_s.pack(side=tk.LEFT, padx=2)

        self.spin_h.delete(0, "end"); self.spin_h.insert(0, str(self.engine.initial_duration // 3600))
        self.spin_m.delete(0, "end"); self.spin_m.insert(0, str((self.engine.initial_duration % 3600) // 60))
        self.spin_s.delete(0, "end"); self.spin_s.insert(0, str(self.engine.initial_duration % 60))

        btn_apply = tk.Button(custom_frame, text="Apply", font=("Helvetica", 10, "bold"),
                              bg="#24283B", fg="#FF8533", activebackground="#2F354F",
                              relief=tk.FLAT, bd=0, padx=8, pady=3, command=self._on_apply_custom)
        btn_apply.pack(side=tk.LEFT, padx=6)

    def _select_preset(self, seconds):
        self.engine.set_duration(seconds, auto_start=True)

    def on_duration_changed(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        self.spin_h.delete(0, "end"); self.spin_h.insert(0, str(h))
        self.spin_m.delete(0, "end"); self.spin_m.insert(0, str(m))
        self.spin_s.delete(0, "end"); self.spin_s.insert(0, str(s))

    def _on_apply_custom(self):
        try:
            h = int(self.spin_h.get())
            m = int(self.spin_m.get())
            s = int(self.spin_s.get())
            total = h * 3600 + m * 60 + s
            if total > 0:
                self.engine.set_duration(total, auto_start=False)
        except ValueError:
            pass

    def on_tick(self, remaining_seconds, formatted_time, progress_ratio):
        self._update_display(formatted_time, progress_ratio)

    def on_state_changed(self, old_state, new_state):
        self._update_state_ui(new_state)

    def on_finished(self, initial_duration, task_name):
        self._update_state_ui(TimerState.FINISHED)

    def _update_display(self, formatted_time, progress_ratio):
        self.lbl_clock.config(text=formatted_time)

    def _update_state_ui(self, state):
        if state == TimerState.RUNNING:
            self.btn_toggle.config(text="⏸ Pause", bg="#238636", fg="#FFFFFF", activebackground="#2EA043")
            self.lbl_status.config(text="● RUNNING", fg="#3FB950")
        elif state == TimerState.PAUSED:
            self.btn_toggle.config(text="▶ Resume", bg="#E95420", fg="#FFFFFF", activebackground="#FF6622")
            self.lbl_status.config(text="❚❚ PAUSED", fg="#FF8533")
        elif state == TimerState.FINISHED:
            self.btn_toggle.config(text="▶ Restart", bg="#E95420", fg="#FFFFFF", activebackground="#FF6622")
            self.lbl_status.config(text="🔔 TIME'S UP!", fg="#F7768E")
        else:
            self.btn_toggle.config(text="▶ Start", bg="#E95420", fg="#FFFFFF", activebackground="#FF6622")
            self.lbl_status.config(text="○ READY", fg="#A9B1D6")

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def hide(self):
        self.root.withdraw()

    def is_visible(self):
        return self.root.winfo_viewable()
