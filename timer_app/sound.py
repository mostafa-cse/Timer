"""
Cross-platform sound alert player for Timer.
Supports Linux (canberra, pipewire, alsa), macOS (afplay), and Windows (winsound).
"""

import os
import sys
import shutil
import subprocess
import threading
import time

MACOS_SOUNDS = [
    "/System/Library/Sounds/Glass.aiff",
    "/System/Library/Sounds/Ping.aiff",
    "/System/Library/Sounds/Hero.aiff",
    "/System/Library/Sounds/Submarine.aiff"
]

LINUX_SOUNDS = [
    "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
    "/usr/share/sounds/freedesktop/stereo/complete.oga",
    "/usr/share/sounds/freedesktop/stereo/bell.oga",
    "/usr/share/sounds/gnome/default/alerts/string.ogg"
]


class SoundPlayer:
    def __init__(self):
        self.platform = sys.platform
        self.canberra = shutil.which("canberra-gtk-play") if self.platform.startswith("linux") else None
        self.pw_play = shutil.which("pw-play") if self.platform.startswith("linux") else None
        self.aplay = shutil.which("aplay") if self.platform.startswith("linux") else None
        self.afplay = shutil.which("afplay") if self.platform == "darwin" else None
        self._current_sound = self._find_best_sound()

    def _find_best_sound(self):
        if self.platform == "darwin":
            for p in MACOS_SOUNDS:
                if os.path.exists(p):
                    return p
        elif self.platform.startswith("linux"):
            for p in LINUX_SOUNDS:
                if os.path.exists(p):
                    return p
        return None

    def play_alarm_async(self, repeats=2, interval=1.2):
        """Play alarm sound in a background daemon thread."""
        thread = threading.Thread(target=self._play_worker, args=(repeats, interval), daemon=True)
        thread.start()

    def _play_worker(self, repeats, interval):
        for i in range(max(1, repeats)):
            self._play_once()
            if i < repeats - 1:
                time.sleep(interval)

    def _play_once(self):
        # 1. Windows
        if self.platform == "win32":
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                return
            except Exception:
                try:
                    subprocess.run(
                        ["powershell", "-c", "[System.Media.SystemSounds]::Exclamation.Play()"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                    )
                    return
                except Exception:
                    pass

        # 2. macOS
        if self.platform == "darwin":
            if self.afplay and self._current_sound:
                try:
                    subprocess.run(
                        [self.afplay, self._current_sound],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                    )
                    return
                except Exception:
                    pass

        # 3. Linux
        if self.platform.startswith("linux"):
            if self.canberra:
                try:
                    subprocess.run(
                        [self.canberra, "-i", "alarm-clock-elapsed"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                    )
                    return
                except Exception:
                    pass

            if self.pw_play and self._current_sound:
                try:
                    subprocess.run(
                        [self.pw_play, self._current_sound],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                    )
                    return
                except Exception:
                    pass

            if self.canberra and self._current_sound:
                try:
                    subprocess.run(
                        [self.canberra, "-f", self._current_sound],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                    )
                    return
                except Exception:
                    pass

        # Fallback bell
        print("\a", end="", flush=True)
