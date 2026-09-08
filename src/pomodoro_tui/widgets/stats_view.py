"""
Statistics and session history dashboard widget.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widget import Widget
from textual.widgets import DataTable, ProgressBar, Static

from pomodoro_tui.models import SessionType
from pomodoro_tui.storage import PomodoroStorage


class StatsWidget(Widget):
    """Visual statistics and past session logs."""

    DEFAULT_CSS = """
    StatsWidget {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    #stats_title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .stats_summary_grid {
        grid-size: 4;
        grid-gutter: 1;
        height: auto;
        margin-bottom: 1;
    }

    .stat_card {
        border: round $primary;
        background: $surface;
        padding: 1;
        align: center middle;
        height: 5;
    }

    .stat_card_value {
        text-align: center;
        text-style: bold;
        color: $success;
    }

    .stat_card_label {
        text-align: center;
        color: $text-muted;
    }

    #goal_container {
        height: auto;
        margin-bottom: 1;
        padding: 0 1;
    }

    #goal_label {
        color: $text;
        margin-bottom: 0;
    }

    #goal_progress_bar {
        width: 100%;
    }

    #history_label {
        text-style: bold;
        color: $warning;
        margin-top: 1;
        margin-bottom: 0;
    }

    #history_table {
        height: 1fr;
        border: solid $accent;
    }
    """

    def __init__(self, storage: PomodoroStorage, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.storage = storage

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("📊 Daily Statistics & History", id="stats_title")

            with Grid(classes="stats_summary_grid"):
                with Vertical(classes="stat_card"):
                    yield Static("0m", id="val_focus_time", classes="stat_card_value")
                    yield Static("Total Focus Today", classes="stat_card_label")

                with Vertical(classes="stat_card"):
                    yield Static("0 / 8", id="val_completed_pomodoros", classes="stat_card_value")
                    yield Static("Pomodoros Completed", classes="stat_card_label")

                with Vertical(classes="stat_card"):
                    yield Static("0", id="val_short_breaks", classes="stat_card_value")
                    yield Static("Short Breaks", classes="stat_card_label")

                with Vertical(classes="stat_card"):
                    yield Static("0", id="val_long_breaks", classes="stat_card_value")
                    yield Static("Long Breaks", classes="stat_card_label")

            with Vertical(id="goal_container"):
                yield Static("Daily Goal Progress (0%)", id="goal_label")
                yield ProgressBar(total=100, show_eta=False, id="goal_progress_bar")

            yield Static("Recent Sessions", id="history_label")
            yield DataTable(id="history_table", cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one("#history_table", DataTable)
        table.add_column("Time", width=18)
        table.add_column("Type", width=16)
        table.add_column("Duration", width=12)
        table.add_column("Linked Task", width=35)
        self.refresh_stats()

    def refresh_stats(self) -> None:
        stats = self.storage.get_today_stats()
        settings = self.storage.load_settings()

        # Update cards
        self.query_one("#val_focus_time", Static).update(stats.formatted_focus_time)

        pomo_str = f"{stats.completed_pomodoros} / {settings.daily_goal}"
        self.query_one("#val_completed_pomodoros", Static).update(pomo_str)

        self.query_one("#val_short_breaks", Static).update(str(stats.short_breaks_count))
        self.query_one("#val_long_breaks", Static).update(str(stats.long_breaks_count))

        # Update Goal progress
        goal = max(1, settings.daily_goal)
        percent = min(100.0, (stats.completed_pomodoros / goal) * 100.0)
        self.query_one("#goal_label", Static).update(
            f"Daily Goal Progress: {stats.completed_pomodoros} of {goal} Pomodoros ({percent:.0f}%)"
        )
        self.query_one("#goal_progress_bar", ProgressBar).progress = percent

        # Update history table
        table = self.query_one("#history_table", DataTable)
        table.clear()
        history = self.storage.get_history(limit=50)

        for s in history:
            # Parse completed_at
            try:
                time_str = s.completed_at.replace("T", " ")[:16]
            except Exception:
                time_str = s.completed_at

            type_icon = s.session_type.icon
            type_name = f"{type_icon} {s.session_type.display_name}"
            dur_min = max(1, s.duration_seconds // 60)
            dur_str = f"{dur_min} min"
            task_str = s.task_title if s.task_title else "-"

            table.add_row(time_str, type_name, dur_str, task_str)
