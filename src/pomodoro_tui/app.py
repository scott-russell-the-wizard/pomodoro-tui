"""
Main application module for Pomodoro TUI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from pomodoro_tui.models import (
    CompletedSession,
    PomodoroSettings,
    SessionType,
    TimerStatus,
)
from pomodoro_tui.notifications import NotificationManager
from pomodoro_tui.storage import PomodoroStorage
from pomodoro_tui.timer import PomodoroTimer
from pomodoro_tui.widgets.controls import TimerControls
from pomodoro_tui.widgets.help_modal import HelpModal
from pomodoro_tui.widgets.settings_modal import SettingsModal
from pomodoro_tui.widgets.stats_view import StatsWidget
from pomodoro_tui.widgets.task_list import TaskListWidget
from pomodoro_tui.widgets.timer_display import TimerDisplay


class PomodoroApp(App):
    """Pomodoro Terminal User Interface Application."""

    TITLE = "Pomodoro TUI"
    SUB_TITLE = "Stay Focused, Take Breaks"
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("space", "toggle_timer", "Start/Pause", priority=True),
        Binding("s", "skip_session", "Skip"),
        Binding("r", "reset_session", "Reset"),
        Binding("equal,plus", "add_minute", "+1m"),
        Binding("minus", "sub_minute", "-1m"),
        Binding("1", "switch_tab('tab_timer')", "Timer"),
        Binding("2", "switch_tab('tab_tasks')", "Tasks"),
        Binding("t", "switch_tab('tab_tasks')", "Tasks"),
        Binding("3", "switch_tab('tab_stats')", "Stats"),
        Binding("c", "open_settings", "Settings"),
        Binding("h", "open_help", "Help"),
        Binding("question_mark", "open_help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        settings: Optional[PomodoroSettings] = None,
        data_dir: Optional[Path] = None,
    ) -> None:
        super().__init__()
        self.storage = PomodoroStorage(data_dir=data_dir)

        # Merge saved settings with passed settings
        if settings is not None:
            self.settings = settings
        else:
            self.settings = self.storage.load_settings()

        self.timer = PomodoroTimer(self.settings)
        self.notifications = NotificationManager(
            sound_enabled=self.settings.sound_enabled,
            desktop_notify=self.settings.desktop_notify,
        )
        self._ticker_interval = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with TabbedContent(initial="tab_timer", id="main_tabs"):
            with TabPane("⏱️ Timer [1]", id="tab_timer"):
                with Vertical(id="timer_view_container"):
                    yield TimerDisplay(id="timer_display")
                    yield TimerControls(id="timer_controls")
                    yield Static(
                        "[dim][Space] Start/Pause  [s] Skip  [r] Reset  [+/-] Time  [c] Settings  [h/?] Help  [q] Quit[/dim]",
                        id="hotkey_bar",
                    )

            with TabPane("📋 Tasks [2]", id="tab_tasks"):
                yield TaskListWidget(self.storage, id="task_list_widget")

            with TabPane("📊 Stats [3]", id="tab_stats"):
                yield StatsWidget(self.storage, id="stats_widget")

        yield Footer()

    def on_mount(self) -> None:
        """Start the interval ticker and refresh initial display."""
        self._update_all_displays()
        self._ticker_interval = self.set_interval(1.0, self._on_tick)

    def _update_all_displays(self) -> None:
        """Update timer display, controls, and active task banner."""
        active_task = self.storage.get_active_task()
        display = self.query_one("#timer_display", TimerDisplay)
        controls = self.query_one("#timer_controls", TimerControls)

        display.update_display(self.timer, active_task=active_task)
        controls.update_status(self.timer.status)

    def _on_tick(self) -> None:
        """Invoked every 1 second by the timer ticker."""
        if self.timer.status != TimerStatus.RUNNING:
            return

        session_finished = self.timer.tick()
        if session_finished:
            self._handle_session_finished()
        else:
            self._update_all_displays()

    def _handle_session_finished(self) -> None:
        """Triggered when a countdown reaches zero."""
        active_task = self.storage.get_active_task()
        finished_type = self.timer.current_type

        # Log session to storage
        session_record = CompletedSession(
            session_type=finished_type,
            duration_seconds=self.timer.total_seconds,
            task_id=active_task.id if active_task else None,
            task_title=active_task.title if active_task else None,
        )
        self.storage.log_session(session_record)

        # If work session, increment task progress
        if finished_type == SessionType.WORK and active_task:
            active_task.pomodoros_completed += 1
            if active_task.pomodoros_completed >= active_task.pomodoros_estimated:
                self.notify(f"Task complete: {active_task.title} 🎉", title="Task Completed")
            self.storage.update_task(active_task)

        # Advance state
        _, next_type = self.timer.advance_session(was_completed=True)

        # Notify
        self.notifications.notify_session_complete(finished_type, next_type)

        if finished_type == SessionType.WORK:
            self.notify(
                f"Completed focus session! Take a {next_type.display_name.lower()}.",
                title="Focus Complete! 🍅",
                severity="information",
            )
        else:
            self.notify(
                "Break over! Ready for next focus session.",
                title="Break Finished ☕",
                severity="information",
            )

        self._update_all_displays()

    # User action bindings & handlers
    def action_toggle_timer(self) -> None:
        """Start or pause the timer."""
        self.timer.toggle()
        self._update_all_displays()

    def action_skip_session(self) -> None:
        """Skip current session immediately."""
        _, next_type = self.timer.advance_session(was_completed=False)
        self.notify(f"Skipped to {next_type.display_name}.", title="Session Skipped")
        self._update_all_displays()

    def action_reset_session(self) -> None:
        """Reset current countdown."""
        self.timer.reset()
        self.notify("Timer reset.", title="Reset")
        self._update_all_displays()

    def action_add_minute(self) -> None:
        """Add 60 seconds to timer."""
        self.timer.adjust_time(60)
        self._update_all_displays()

    def action_sub_minute(self) -> None:
        """Subtract 60 seconds from timer."""
        self.timer.adjust_time(-60)
        self._update_all_displays()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch active tab in TabbedContent."""
        tabs = self.query_one("#main_tabs", TabbedContent)
        tabs.active = tab_id
        if tab_id == "tab_tasks":
            self.query_one("#task_list_widget", TaskListWidget).refresh_tasks()
        elif tab_id == "tab_stats":
            self.query_one("#stats_widget", StatsWidget).refresh_stats()

    def action_open_settings(self) -> None:
        """Show settings modal."""
        def handle_settings_result(new_settings: Optional[PomodoroSettings]) -> None:
            if new_settings is not None:
                self.settings = new_settings
                self.storage.save_settings(new_settings)
                self.timer.update_settings(new_settings)
                self.notifications.sound_enabled = new_settings.sound_enabled
                self.notifications.desktop_notify = new_settings.desktop_notify
                self._update_all_displays()
                self.notify("Settings updated!", title="Saved", severity="information")

        self.push_screen(SettingsModal(self.settings), handle_settings_result)

    def action_open_help(self) -> None:
        """Show help modal."""
        self.push_screen(HelpModal())

    # Messages from child widgets
    def on_timer_controls_toggle_requested(self, message: TimerControls.ToggleRequested) -> None:
        self.action_toggle_timer()

    def on_timer_controls_skip_requested(self, message: TimerControls.SkipRequested) -> None:
        self.action_skip_session()

    def on_timer_controls_reset_requested(self, message: TimerControls.ResetRequested) -> None:
        self.action_reset_session()

    def on_timer_controls_adjust_time_requested(self, message: TimerControls.AdjustTimeRequested) -> None:
        self.timer.adjust_time(message.delta_seconds)
        self._update_all_displays()

    def on_task_list_widget_active_task_changed(self, message: TaskListWidget.ActiveTaskChanged) -> None:
        self._update_all_displays()
        if message.task:
            self.notify(f"Active task set: {message.task.title}", title="Task Activated")
        else:
            self.notify("Active task cleared.", title="Task Cleared")
