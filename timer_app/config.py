"""
Configuration manager for Timer.
Cross-platform settings persistence for Linux, macOS, and Windows.
"""

import json
import os
import sys
from pathlib import Path

DEFAULT_CONFIG = {
    "default_duration_seconds": 1500,  # 25 minutes default
    "sound_enabled": True,
    "sound_repeats": 2,
    "notify_critical": True,
    "show_window_on_start": True,
    "keep_tray_when_idle": True,
    "recent_presets": [300, 600, 900, 1500, 1800, 2700, 3600]
}


def get_config_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "Timer"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Timer"
    else:
        # Linux / Unix
        legacy = Path.home() / ".config" / "ubuntu-topbar-timer"
        current = Path.home() / ".config" / "timer"
        if legacy.exists() and not current.exists():
            return legacy
        return current


CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    def __init__(self):
        self.data = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
        except Exception as e:
            print(f"[Config] Error loading config: {e}")

    def save(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[Config] Error saving config: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.data[key] = value
        self.save()
