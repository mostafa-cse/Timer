# ⏱ Timer

**Timer** is an ultra-efficient, lightweight, cross-platform countdown timer and Pomodoro tracker built for **Ubuntu / Linux**, **macOS**, and **Windows**.

It provides native top bar / menu bar / system tray integration displaying live **`Hour:minutes:seconds` (`HH:MM:SS`)**, along with audible alerts and rich desktop notifications when your timer finishes.

---

## 🌟 Platform Features

| Feature | 🐧 Ubuntu / Linux | 🍎 macOS | 🪟 Windows |
|---|---|---|---|
| **Top Bar / Tray Display** | Native Top Bar (`00:25:00` live text) | Menu Bar (`00:25:00` live title) | System Tray (dynamic icon & live tooltip) |
| **Desktop Notifications** | GNOME Shell Desktop Notifications | Native macOS Notifications | Windows 10/11 Toast Notifications |
| **Audio Alert on Finish** | Canberra / PipeWire / ALSA chime | macOS System Sound (`Glass.aiff`) | Windows System Exclamation / Sound |
| **Control Center GUI** | Native Ubuntu Yaru GTK3 Window | Dark-mode Tkinter Window | Dark-mode Tkinter Window |
| **Command Line Interface** | `timer 25m`, `timer +5m`, `timer --toggle` | `python3 run.py 25m` | `python run.py 25m` |
| **Installer** | `.deb` package & shell installer | `.app` bundle & `.dmg` | `Timer.exe` standalone |

---

## 🚀 Quick Start

### 🐧 Ubuntu / Linux

#### Installation via `.deb` package:
```bash
sudo apt install ./timer_1.0.0_all.deb
# or
sudo dpkg -i ./timer_1.0.0_all.deb
```

#### User Installation (no `sudo` required):
```bash
./install.sh
```

#### Launching:
- Search for **"Timer"** in Ubuntu Applications (Super / Win key)
- Or run in terminal:
  ```bash
  timer                 # Open Timer window
  timer 25m             # Start 25-minute Pomodoro in top bar
  timer 10s             # Quick 10-second test
  timer +5m             # Add 5 minutes to active timer
  timer --toggle        # Pause / Resume
  timer --reset         # Reset timer
  ```

---

### 🪟 Windows

1. Download `Timer-windows-x64.zip` from [Releases](../../releases).
2. Extract and run `Timer.exe`.
3. To build from source on Windows:
   ```cmd
   build_windows.bat
   ```

---

### 🍎 macOS

1. Download `Timer-macos.zip` from [Releases](../../releases).
2. Unzip and drag `Timer.app` into your Applications folder.
3. To build from source on macOS:
   ```bash
   chmod +x build_macos.sh
   ./build_macos.sh
   ```

---

## ⚡ GitHub Actions & Automated Releases

This repository includes a multi-platform CI/CD release workflow ([`.github/workflows/release.yml`](.github/workflows/release.yml)).

Whenever a version tag is pushed (e.g., `v1.0.0`), GitHub Actions automatically:
1. Builds the **Ubuntu `.deb` package** (`timer_1.0.0_all.deb`) and Linux tarball.
2. Builds the **Windows single-file executable** (`Timer-windows-x64.zip`).
3. Builds the **macOS Application bundle** (`Timer-macos.zip`).
4. Creates a new **GitHub Release** and publishes all artifacts automatically!

### How to Release a New Version to GitHub:
```bash
# 1. Add your GitHub remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/Timer.git

# 2. Push main branch
git push -u origin main

# 3. Create and push a version tag to trigger automated release
git tag v1.0.0
git push origin v1.0.0
```

---

## 📁 Repository Structure

```
Timer/
├── .github/
│   └── workflows/
│       └── release.yml     # Automated cross-platform GitHub Actions release workflow
├── timer_app/
│   ├── __init__.py
│   ├── core.py             # Precision monotonic countdown engine
│   ├── config.py           # Cross-platform settings persistence
│   ├── sound.py            # Linux, macOS, and Windows sound alerts
│   ├── notifier.py         # Cross-platform desktop notifications
│   ├── sni.py              # Ubuntu top bar StatusNotifierItem with live 'HH:MM:SS'
│   ├── tray.py             # Unified platform tray abstraction
│   ├── gui.py              # Ubuntu native GTK3 Yaru interface
│   ├── gui_crossplatform.py# Universal dark-mode Tkinter interface for Windows/macOS
│   └── app.py              # Main application coordinator
├── assets/
│   ├── timer.svg           # High-resolution vector icon
│   ├── timer.png           # 512x512 PNG app icon
│   ├── timer.ico           # Multi-resolution Windows icon
│   └── timer-symbolic.svg  # Top bar symbolic icon
├── build_deb.sh            # Ubuntu .deb builder script
├── build_windows.bat       # Windows PyInstaller build script
├── build_macos.sh          # macOS build script
├── install.sh              # Ubuntu universal installer
├── uninstall.sh            # Clean uninstaller
├── timer.desktop           # Linux desktop launcher
├── run.py                  # Main entry point & CLI
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
└── README.md               # Documentation
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
