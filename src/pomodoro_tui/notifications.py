"""
Notification dispatcher for audio bell, OSC terminal notifications, and desktop alerts.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from typing import Callable, Optional
from pomodoro_tui.models import SessionType


class NotificationManager:
    """Dispatches sound, OSC terminal escape alerts, and desktop notifications."""

    def __init__(self, sound_enabled: bool = True, desktop_notify: bool = False) -> None:
        self.sound_enabled = sound_enabled
        self.desktop_notify = desktop_notify
        self._notify_send_path = shutil.which("notify-send")

    def play_bell(self, terminal_write: Optional[Callable[[str], None]] = None) -> None:
        """Trigger terminal visual/audible bell.

        Writes 3 BEL pulses through the terminal driver (or stdout fallback).
        """
        if not self.sound_enabled:
            return

        bell_seq = "\07\07\07"
        if terminal_write is not None:
            try:
                terminal_write(bell_seq)
            except Exception:
                pass

        try:
            sys.stdout.write(bell_seq)
            sys.stdout.flush()
        except Exception:
            pass

    def send_osc_notification(
        self,
        title: str,
        message: str,
        terminal_write: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Send OSC 9 and OSC 777 notification escape sequences.

        These sequences are interpreted by SSH client terminals (e.g. iTerm2,
        macOS Terminal, Windows Terminal, Kitty, WezTerm) to trigger a native
        desktop notification on the user's local machine even over remote SSH.
        """
        clean_title = title.replace(";", " ").replace("\n", " ")
        clean_msg = message.replace(";", " ").replace("\n", " ")

        # OSC 9: supported by iTerm2, Windows Terminal, etc.
        osc_9 = f"\033]9;{clean_title}: {clean_msg}\007"
        # OSC 777: supported by Kitty, WezTerm, Foot, etc.
        osc_777 = f"\033]777;notify;{clean_title};{clean_msg}\007"

        combined = osc_9 + osc_777

        if terminal_write is not None:
            try:
                terminal_write(combined)
            except Exception:
                pass

        try:
            sys.stdout.write(combined)
            sys.stdout.flush()
        except Exception:
            pass

    def send_desktop_notification(self, title: str, message: str) -> None:
        """Trigger Linux desktop notification via notify-send if available."""
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

    def notify_session_complete(
        self,
        finished_type: SessionType,
        next_type: SessionType,
        terminal_write: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Called when a pomodoro interval reaches zero."""
        if finished_type == SessionType.WORK:
            title = "Focus Session Complete! 🍅"
            msg = f"Great job! Time for a {next_type.display_name.lower()}."
        elif finished_type == SessionType.SHORT_BREAK:
            title = "Short Break Over ☕"
            msg = "Ready to start your next focus session?"
        else:
            title = "Long Break Over 🌴"
            msg = "Feeling refreshed? Time to dive back in!"

        # 1. Ring console bell
        self.play_bell(terminal_write=terminal_write)

        # 2. Send OSC escape sequences for SSH client notification
        self.send_osc_notification(title, msg, terminal_write=terminal_write)

        # 3. Trigger local notify-send if available
        self.send_desktop_notification(title, msg)
