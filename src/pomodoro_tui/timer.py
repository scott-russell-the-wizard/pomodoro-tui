"""
Core Pomodoro timer state machine and interval management.
"""

from __future__ import annotations

from typing import Tuple
from pomodoro_tui.models import SessionType, TimerStatus, PomodoroSettings


class PomodoroTimer:
    """Manages Pomodoro intervals, countdown logic, and state transitions."""

    def __init__(self, settings: PomodoroSettings) -> None:
        self.settings = settings
        self.current_type: SessionType = SessionType.WORK
        self.status: TimerStatus = TimerStatus.STOPPED
        self.session_index: int = 1
        self.cycle_count: int = 1
        self.completed_work_sessions: int = 0

        self.total_seconds: int = self._get_duration_for_type(self.current_type)
        self.remaining_seconds: int = self.total_seconds

    def _get_duration_for_type(self, session_type: SessionType) -> int:
        if session_type == SessionType.WORK:
            return max(1, self.settings.work_minutes * 60)
        elif session_type == SessionType.SHORT_BREAK:
            return max(1, self.settings.short_break_minutes * 60)
        elif session_type == SessionType.LONG_BREAK:
            return max(1, self.settings.long_break_minutes * 60)
        return 1500

    def start(self) -> None:
        """Start or resume the countdown."""
        self.status = TimerStatus.RUNNING

    def pause(self) -> None:
        """Pause the countdown."""
        if self.status == TimerStatus.RUNNING:
            self.status = TimerStatus.PAUSED

    def toggle(self) -> TimerStatus:
        """Toggle between RUNNING and PAUSED/STOPPED."""
        if self.status == TimerStatus.RUNNING:
            self.pause()
        else:
            self.start()
        return self.status

    def reset(self) -> None:
        """Reset current interval to initial full duration and stop."""
        self.status = TimerStatus.STOPPED
        self.total_seconds = self._get_duration_for_type(self.current_type)
        self.remaining_seconds = self.total_seconds

    def adjust_time(self, delta_seconds: int) -> None:
        """Add or subtract seconds from remaining time (e.g. +60s / -60s)."""
        new_remaining = self.remaining_seconds + delta_seconds
        new_remaining = max(0, min(new_remaining, 99 * 60 + 59))
        self.remaining_seconds = new_remaining
        if new_remaining > self.total_seconds:
            self.total_seconds = new_remaining

    def tick(self) -> bool:
        """Decrement by 1 second if running. Returns True if interval reached zero."""
        if self.status != TimerStatus.RUNNING:
            return False

        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1

        if self.remaining_seconds <= 0:
            return True

        return False

    def advance_session(self, was_completed: bool = True) -> Tuple[SessionType, SessionType]:
        """Advance to the next session. Returns (finished_type, next_type)."""
        finished_type = self.current_type

        if finished_type == SessionType.WORK:
            if was_completed:
                self.completed_work_sessions += 1

            if (
                self.settings.long_break_interval > 0
                and self.completed_work_sessions > 0
                and self.completed_work_sessions % self.settings.long_break_interval == 0
            ):
                next_type = SessionType.LONG_BREAK
            else:
                next_type = SessionType.SHORT_BREAK
        else:
            # We were on break, now go to work
            if finished_type == SessionType.LONG_BREAK:
                self.cycle_count += 1
                self.session_index = 1
            else:
                self.session_index += 1
            next_type = SessionType.WORK

        self.current_type = next_type
        self.total_seconds = self._get_duration_for_type(next_type)
        self.remaining_seconds = self.total_seconds

        # Check auto start
        if next_type == SessionType.WORK:
            should_auto = self.settings.auto_start_work
        else:
            should_auto = self.settings.auto_start_breaks

        self.status = TimerStatus.RUNNING if should_auto else TimerStatus.STOPPED
        return finished_type, next_type

    def update_settings(self, new_settings: PomodoroSettings) -> None:
        """Apply new settings and update current session duration if stopped."""
        self.settings = new_settings
        if self.status == TimerStatus.STOPPED:
            self.reset()

    @property
    def progress_fraction(self) -> float:
        """Completion fraction from 0.0 (just started) to 1.0 (finished)."""
        if self.total_seconds <= 0:
            return 1.0
        elapsed = self.total_seconds - self.remaining_seconds
        return max(0.0, min(1.0, elapsed / self.total_seconds))

    @property
    def formatted_time(self) -> str:
        """Formatted string MM:SS."""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def cycle_dots(self) -> str:
        """Visual representation of work sessions completed in current cycle."""
        interval = max(1, self.settings.long_break_interval)
        # Completed in this cycle:
        done_in_cycle = self.completed_work_sessions % interval
        # If we just reached long break, all interval dots are full:
        if self.current_type == SessionType.LONG_BREAK:
            done_in_cycle = interval

        dots = []
        for i in range(interval):
            if i < done_in_cycle:
                dots.append("●")
            else:
                dots.append("○")
        return " ".join(dots)
