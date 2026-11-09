"""
Universal Cross-Platform GUI Window for Timer (Windows, macOS, fallback).
Built using Python's standard Tkinter with a sleek dark theme.
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
        self.root.geometry("400x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#2E3440")

        # Handle window close (minimize instead of quit)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

        self._build_ui()
        self._update_display(self.engine.get_formatted_time(), 0.0)
        self._update_state_ui(self.engine.state)

    def _build_ui(self):
        # 1. Header Frame
        header = tk.Frame(self.root, bg="#3B4252", height=45)
        header.pack(fill=tk.X, side=tk.TOP)
        lbl_title = tk.Label(header, text="Timer", font=("Helvetica", 14, "bold"), fg="#ECEFF4", bg="#3B4252")
        lbl_title.pack(side=tk.LEFT, padx=16, pady=8)

        btn_min = tk.Button(header, text="—", font=("Helvetica", 10), fg="#D8DEE9", bg="#4C566A",
                            relief=tk.FLAT, command=self.hide)
        btn_min.pack(side=tk.RIGHT, padx=12, pady=8)

        # 2. Main Container
        main = tk.Frame(self.root, bg="#2E3440")
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        # Digital Clock
        self.lbl_clock = tk.Label(main, text="00:25:00", font=("Courier", 38, "bold"),
                                  fg="#E95420", bg="#2E3440")
        self.lbl_clock.pack(pady=(10, 4))

        self.lbl_status = tk.Label(main, text="Ready", font=("Helvetica", 10),
                                   fg="#88C0D0", bg="#2E3440")
        self.lbl_status.pack(pady=(0, 12))

        # Action Buttons (Start / Pause / Reset)
        btn_frame = tk.Frame(main, bg="#2E3440")
        btn_frame.pack(fill=tk.X, pady=8)

        self.btn_toggle = tk.Button(btn_frame, text="▶ Start", font=("Helvetica", 12, "bold"),
                                    bg="#E95420", fg="#FFFFFF", relief=tk.FLAT, padx=16, pady=8,
                                    command=self.controller.on_action_toggle)
        self.btn_toggle.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

        self.btn_reset = tk.Button(btn_frame, text="⏹ Reset", font=("Helvetica", 12),
                                   bg="#4C566A", fg="#ECEFF4", relief=tk.FLAT, padx=16, pady=8,
                                   command=self.controller.on_action_reset)
        self.btn_reset.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

        # Quick Adjustments (+1m, +5m, +10m)
        adj_frame = tk.Frame(main, bg="#2E3440")
        adj_frame.pack(fill=tk.X, pady=6)
        for text, secs in [("+1m", 60), ("+5m", 300), ("+10m", 600)]:
            b = tk.Button(adj_frame, text=text, font=("Helvetica", 10), bg="#434C5E", fg="#D8DEE9",
                          relief=tk.FLAT, command=lambda s=secs: self.engine.add_seconds(s))
            b.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        # Presets Section
        lbl_presets = tk.Label(main, text="Quick Presets", font=("Helvetica", 11, "bold"),
                               fg="#D8DEE9", bg="#2E3440", anchor="w")
        lbl_presets.pack(fill=tk.X, pady=(12, 6))

        pres_grid = tk.Frame(main, bg="#2E3440")
        pres_grid.pack(fill=tk.X)

        presets = [
            ("5m", 300), ("10m", 600), ("15m", 900), ("25m 🍅", 1500),
            ("30m", 1800), ("45m", 2700), ("1h", 3600), ("2h", 7200)
        ]
        for idx, (label, secs) in enumerate(presets):
            row = idx // 4
            col = idx % 4
            b = tk.Button(pres_grid, text=label, font=("Helvetica", 9), bg="#3B4252", fg="#ECEFF4",
                          relief=tk.FLAT, command=lambda s=secs: self._select_preset(s))
            b.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            pres_grid.grid_columnconfigure(col, weight=1)

        # Custom Time Frame
        custom_frame = tk.Frame(main, bg="#2E3440")
        custom_frame.pack(fill=tk.X, pady=(16, 8))

        lbl_custom = tk.Label(custom_frame, text="Set H:M:S:", font=("Helvetica", 10),
                              fg="#D8DEE9", bg="#2E3440")
        lbl_custom.pack(side=tk.LEFT, padx=4)

        self.spin_h = tk.Spinbox(custom_frame, from_=0, to=99, width=3, font=("Helvetica", 11))
        self.spin_h.pack(side=tk.LEFT, padx=2)
        self.spin_m = tk.Spinbox(custom_frame, from_=0, to=59, width=3, font=("Helvetica", 11))
        self.spin_m.pack(side=tk.LEFT, padx=2)
        self.spin_s = tk.Spinbox(custom_frame, from_=0, to=59, width=3, font=("Helvetica", 11))
        self.spin_s.pack(side=tk.LEFT, padx=2)

        self.spin_h.delete(0, "end"); self.spin_h.insert(0, str(self.engine.initial_duration // 3600))
        self.spin_m.delete(0, "end"); self.spin_m.insert(0, str((self.engine.initial_duration % 3600) // 60))
        self.spin_s.delete(0, "end"); self.spin_s.insert(0, str(self.engine.initial_duration % 60))

        btn_apply = tk.Button(custom_frame, text="Set", font=("Helvetica", 10, "bold"),
                              bg="#5E81AC", fg="#ECEFF4", relief=tk.FLAT, command=self._on_apply_custom)
        btn_apply.pack(side=tk.LEFT, padx=6)

    def _select_preset(self, seconds):
        self.engine.set_duration(seconds, auto_start=True)

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
            self.btn_toggle.config(text="⏸ Pause", bg="#A3BE8C", fg="#2E3440")
            self.lbl_status.config(text="🟢 Running", fg="#A3BE8C")
        elif state == TimerState.PAUSED:
            self.btn_toggle.config(text="▶ Resume", bg="#EBCB8B", fg="#2E3440")
            self.lbl_status.config(text="⏸ Paused", fg="#EBCB8B")
        elif state == TimerState.FINISHED:
            self.btn_toggle.config(text="▶ Restart", bg="#BF616A", fg="#FFFFFF")
            self.lbl_status.config(text="🔔 Finished!", fg="#BF616A")
        else:
            self.btn_toggle.config(text="▶ Start", bg="#E95420", fg="#FFFFFF")
            self.lbl_status.config(text="⚪ Ready", fg="#88C0D0")

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def hide(self):
        self.root.withdraw()

    def is_visible(self):
        return self.root.winfo_viewable()
