"""
Timer display widget with big digits, session badges, progress bar, and cycle indicators.
"""

from __future__ import annotations

from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widget import Widget
from textual.widgets import Digits, ProgressBar, Static

from pomodoro_tui.models import SessionType, TimerStatus, Task
from pomodoro_tui.timer import PomodoroTimer


class TimerDisplay(Widget):
    """Main visual timer display."""

    DEFAULT_CSS = """
    TimerDisplay {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 2;
    }

    #timer_card {
        width: 100%;
        max-width: 80;
        height: auto;
        border: heavy $accent;
        background: $surface;
        padding: 1 2;
        align: center middle;
    }

    #session_type_badge {
        text-align: center;
        text-style: bold;
        margin-bottom: 0;
        color: $accent;
    }

    #status_badge {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    #digits_display {
        text-align: center;
        margin: 1 0;
        min-height: 5;
    }

    #progress_bar {
        width: 100%;
        margin: 1 0;
    }

    #cycle_status {
        text-align: center;
        text-style: bold;
        color: $secondary;
        margin-top: 1;
    }

    #active_task_banner {
        text-align: center;
        margin-top: 1;
        color: $text;
        background: $panel;
        padding: 0 1;
        border: round $primary;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="timer_card"):
            yield Static("🍅 Focus Session", id="session_type_badge")
            yield Static("[ READY ]", id="status_badge")
            yield Digits("25:00", id="digits_display")
            yield ProgressBar(total=100, show_eta=False, id="progress_bar")
            yield Static("Cycle 1 • Pomodoro 1 of 4   ○ ○ ○ ○", id="cycle_status")
            yield Static("🎯 Active Task: None (press 't' to select)", id="active_task_banner")

    def update_display(self, timer: PomodoroTimer, active_task: Optional[Task] = None) -> None:
        """Update all display elements based on timer and active task."""
        # 1. Session badge
        type_badge = self.query_one("#session_type_badge", Static)
        session_name = f"{timer.current_type.icon} {timer.current_type.display_name}"
        type_badge.update(session_name)

        # 2. Status badge
        status_badge = self.query_one("#status_badge", Static)
        if timer.status == TimerStatus.RUNNING:
            status_text = "[bold green][ RUNNING ][/]"
        elif timer.status == TimerStatus.PAUSED:
            status_text = "[bold yellow][ PAUSED ][/]"
        else:
            status_text = "[bold blue][ READY ][/]"
        status_badge.update(status_text)

        # 3. Digits
        digits = self.query_one("#digits_display", Digits)
        digits.update(timer.formatted_time)

        # 4. Progress bar
        pbar = self.query_one("#progress_bar", ProgressBar)
        percent = timer.progress_fraction * 100.0
        pbar.progress = percent

        # 5. Cycle status
        cycle_badge = self.query_one("#cycle_status", Static)
        interval = max(1, timer.settings.long_break_interval)
        current_session = (timer.completed_work_sessions % interval) + 1
        if timer.current_type != SessionType.WORK:
            cycle_text = f"Cycle {timer.cycle_count} • Break Time  [{timer.cycle_dots}]"
        else:
            cycle_text = f"Cycle {timer.cycle_count} • Session {current_session} of {interval}  [{timer.cycle_dots}]"
        cycle_badge.update(cycle_text)

        # 6. Active task
        task_banner = self.query_one("#active_task_banner", Static)
        if active_task:
            task_banner.update(
                f"🎯 Active Task: [bold]{active_task.title}[/] ({active_task.pomodoros_completed}/{active_task.pomodoros_estimated} 🍅)"
            )
        else:
            task_banner.update("🎯 Active Task: None (Press [bold]t[/bold] to manage tasks)")
