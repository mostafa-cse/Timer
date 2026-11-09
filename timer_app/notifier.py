"""
Cross-platform desktop notification sender for Timer.
Supports Linux (libnotify/notify-send), macOS (AppleScript), and Windows (PowerShell/Toasts).
"""

import sys
import shutil
import subprocess

# Linux GI notify import
HAS_GI_NOTIFY = False
if sys.platform.startswith("linux"):
    try:
        import gi
        gi.require_version('Notify', '0.7')
        from gi.repository import Notify
        HAS_GI_NOTIFY = True
    except Exception:
        HAS_GI_NOTIFY = False


class Notifier:
    def __init__(self, on_restart_callback=None):
        self.platform = sys.platform
        self.on_restart_callback = on_restart_callback
        self._notify_initialized = False

        if HAS_GI_NOTIFY:
            try:
                Notify.init("Timer")
                self._notify_initialized = True
            except Exception as e:
                print(f"[Notifier] Failed to init libnotify: {e}")

    def send_timer_finished(self, total_seconds, task_name=None):
        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

        title = f"⏰ Timer Finished: {time_str}"
        if task_name:
            body = f"Your timer for '{task_name}' has ended."
        else:
            body = f"Your {time_str} countdown has reached zero."

        # 1. Windows Notification
        if self.platform == "win32":
            return self._send_windows_toast(title, body)

        # 2. macOS Notification
        if self.platform == "darwin":
            return self._send_macos_notification(title, body)

        # 3. Linux Notification
        return self._send_linux_notification(title, body)

    def _send_linux_notification(self, title, body):
        if self._notify_initialized:
            try:
                notif = Notify.Notification.new(title, body, "alarm-symbolic")
                notif.set_urgency(Notify.Urgency.CRITICAL)
                notif.set_timeout(Notify.EXPIRES_NEVER)
                if self.on_restart_callback:
                    notif.add_action("restart", "Restart Timer", self._on_action_restart, None)
                notif.show()
                return True
            except Exception as e:
                print(f"[Notifier] GI notification error: {e}")

        notify_send = shutil.which("notify-send")
        if notify_send:
            try:
                cmd = [
                    notify_send,
                    "-u", "critical",
                    "-a", "Timer",
                    "-i", "alarm-symbolic",
                    title,
                    body
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception as e:
                print(f"[Notifier] notify-send error: {e}")
        return False

    def _send_macos_notification(self, title, body):
        try:
            # Escape quotes
            safe_title = title.replace('"', '\\"')
            safe_body = body.replace('"', '\\"')
            script = f'display notification "{safe_body}" with title "{safe_title}" sound name "Glass"'
            subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"[Notifier] macOS notification error: {e}")
            return False

    def _send_windows_toast(self, title, body):
        try:
            # Use PowerShell Windows.UI.Notifications
            ps_script = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            $template = @"
            <toast>
                <visual>
                    <binding template="ToastGeneric">
                        <text>{title}</text>
                        <text>{body}</text>
                    </binding>
                </visual>
                <audio src="ms-winsoundevent:Notification.Looping.Alarm" loop="false"/>
            </toast>
"@
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Timer").Show($toast)
            """
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_script],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"[Notifier] Windows toast error: {e}")
            return False

    def _on_action_restart(self, notification, action, user_data):
        if self.on_restart_callback:
            self.on_restart_callback()
