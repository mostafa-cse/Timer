"""
Core Timer Engine for Ubuntu Top Bar Timer.
Drift-free, monotonic clock-based countdown with GLib event loop integration.
"""

import time
from enum import Enum
from gi.repository import GLib


class TimerState(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


class TimerEngine:
    def __init__(self, initial_duration=1500):
        self.initial_duration = max(1, initial_duration)
        self.remaining_seconds = self.initial_duration
        self.target_time = None
        self.state = TimerState.IDLE
        self.task_name = ""

        self._glib_source_id = None
        self.listeners = []

    def add_listener(self, listener):
        """Add callback listener object with on_tick, on_finished, on_state_changed."""
        if listener not in self.listeners:
            self.listeners.append(listener)

    def remove_listener(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)

    def _notify_tick(self):
        progress = 1.0 - (self.remaining_seconds / self.initial_duration) if self.initial_duration > 0 else 0.0
        progress = max(0.0, min(1.0, progress))
        formatted = self.get_formatted_time()
        for l in self.listeners:
            if hasattr(l, "on_tick"):
                l.on_tick(self.remaining_seconds, formatted, progress)

    def _notify_state_changed(self, old_state, new_state):
        for l in self.listeners:
            if hasattr(l, "on_state_changed"):
                l.on_state_changed(old_state, new_state)

    def _notify_finished(self):
        for l in self.listeners:
            if hasattr(l, "on_finished"):
                l.on_finished(self.initial_duration, self.task_name)

    def set_duration(self, seconds, auto_start=False):
        seconds = max(1, int(seconds))
        self.initial_duration = seconds
        self.remaining_seconds = seconds
        if self.state == TimerState.RUNNING:
            self.target_time = time.monotonic() + self.remaining_seconds
        else:
            self.state = TimerState.IDLE
        self._notify_tick()
        if auto_start:
            self.start()

    def set_task_name(self, name):
        self.task_name = str(name).strip()

    def add_seconds(self, seconds):
        if self.state in (TimerState.RUNNING, TimerState.PAUSED):
            self.remaining_seconds = max(1, self.remaining_seconds + seconds)
            self.initial_duration = max(self.initial_duration, self.remaining_seconds)
            if self.state == TimerState.RUNNING:
                self.target_time = time.monotonic() + self.remaining_seconds
            self._notify_tick()
        elif self.state in (TimerState.IDLE, TimerState.FINISHED):
            self.set_duration(self.initial_duration + seconds)

    def start(self, seconds=None):
        if seconds is not None:
            self.set_duration(seconds)

        if self.remaining_seconds <= 0:
            self.remaining_seconds = self.initial_duration

        old_state = self.state
        self.target_time = time.monotonic() + self.remaining_seconds
        self.state = TimerState.RUNNING

        if self._glib_source_id is None:
            self._glib_source_id = GLib.timeout_add_seconds(1, self._on_interval_tick)

        self._notify_state_changed(old_state, self.state)
        self._notify_tick()

    def pause(self):
        if self.state == TimerState.RUNNING:
            old_state = self.state
            # Compute exact remaining integer seconds
            if self.target_time is not None:
                now = time.monotonic()
                diff = self.target_time - now
                self.remaining_seconds = max(0, int(round(diff)))
            self.state = TimerState.PAUSED
            self._stop_glib_source()
            self._notify_state_changed(old_state, self.state)
            self._notify_tick()

    def resume(self):
        if self.state == TimerState.PAUSED:
            self.start()

    def toggle(self):
        if self.state == TimerState.RUNNING:
            self.pause()
        elif self.state in (TimerState.PAUSED, TimerState.IDLE, TimerState.FINISHED):
            self.start()

    def reset(self):
        old_state = self.state
        self._stop_glib_source()
        self.state = TimerState.IDLE
        self.remaining_seconds = self.initial_duration
        self.target_time = None
        self._notify_state_changed(old_state, self.state)
        self._notify_tick()

    def _stop_glib_source(self):
        if self._glib_source_id is not None:
            GLib.source_remove(self._glib_source_id)
            self._glib_source_id = None

    def _on_interval_tick(self):
        if self.state != TimerState.RUNNING:
            self._glib_source_id = None
            return False

        now = time.monotonic()
        remaining = int(round(self.target_time - now))

        if remaining <= 0:
            self.remaining_seconds = 0
            self.state = TimerState.FINISHED
            self._stop_glib_source()
            self._notify_tick()
            self._notify_finished()
            self._notify_state_changed(TimerState.RUNNING, self.state)
            return False
        else:
            self.remaining_seconds = remaining
            self._notify_tick()
            return True

    def get_formatted_time(self):
        """Returns time formatted as Hour:minutes:seconds (HH:MM:SS)."""
        s = max(0, self.remaining_seconds)
        hours = s // 3600
        mins = (s % 3600) // 60
        secs = s % 60
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    @staticmethod
    def parse_time_string(time_str):
        """
        Parses time string formats:
        - "25m" -> 1500
        - "1h30m" -> 5400
        - "45s" -> 45
        - "01:15:30" -> 4530
        - "25:00" -> 1500
        - "300" -> 300
        """
        s = time_str.strip().lower()
        if not s:
            return None

        # Format: HH:MM:SS or MM:SS
        if ":" in s:
            parts = s.split(":")
            if len(parts) == 3:
                try:
                    h, m, sec = map(int, parts)
                    return h * 3600 + m * 60 + sec
                except ValueError:
                    return None
            elif len(parts) == 2:
                try:
                    m, sec = map(int, parts)
                    return m * 60 + sec
                except ValueError:
                    return None

        # Suffix formats: 1h, 25m, 30s, 1h30m
        import re
        total = 0
        matches = re.findall(r'(\d+)\s*([hms])', s)
        if matches:
            for val, unit in matches:
                v = int(val)
                if unit == 'h':
                    total += v * 3600
                elif unit == 'm':
                    total += v * 60
                elif unit == 's':
                    total += v
            return total if total > 0 else None

        # Just integer seconds or minutes? If < 60 and no units, check if user meant minutes
        if s.isdigit():
            val = int(s)
            # If user types "25", usually means 25 minutes
            if val <= 180:
                return val * 60
            return val

        return None
