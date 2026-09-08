"""
Notification dispatcher for audio bell and desktop alerts.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pomodoro_tui.models import SessionType


class NotificationManager:
    """Dispatches sound and desktop alerts."""

    def __init__(self, sound_enabled: bool = True, desktop_notify: bool = False) -> None:
        self.sound_enabled = sound_enabled
        self.desktop_notify = desktop_notify
        self._notify_send_path = shutil.which("notify-send")

    def play_bell(self) -> None:
        """Trigger terminal visual/audible bell."""
        if not self.sound_enabled:
            return
        try:
            sys.stdout.write("\a")
            sys.stdout.flush()
        except Exception:
            pass

    def send_notification(self, title: str, message: str) -> None:
        """Trigger desktop notification if configured and available."""
        if not self.desktop_notify or not self._notify_send_path:
            return
        try:
            subprocess.Popen(
                [self._notify_send_path, "-a", "Pomodoro TUI", title, message],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def notify_session_complete(self, finished_type: SessionType, next_type: SessionType) -> None:
        """Convenience method called when a pomodoro interval completes."""
        self.play_bell()

        if finished_type == SessionType.WORK:
            title = "Focus Session Complete! 🍅"
            msg = f"Great job! Time for a {next_type.display_name.lower()}."
        elif finished_type == SessionType.SHORT_BREAK:
            title = "Short Break Over ☕"
            msg = "Ready to start your next focus session?"
        else:
            title = "Long Break Over 🌴"
            msg = "Feeling refreshed? Time to dive back in!"

        self.send_notification(title, msg)
