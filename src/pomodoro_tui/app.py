"""
Main application module for Pomodoro TUI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from pomodoro_tui.models import (
    CompletedSession,
    PomodoroSettings,
    SessionType,
    Task,
    TimerStatus,
)
from pomodoro_tui.notifications import NotificationManager
from pomodoro_tui.storage import PomodoroStorage
from pomodoro_tui.timer import PomodoroTimer
from pomodoro_tui.widgets.add_task_modal import AddTaskModal
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
        Binding("a", "open_add_task", "Add Task"),
        Binding("1", "switch_tab('tab_timer')", "Timer"),
        Binding("2,t", "switch_tab('tab_tasks')", "Tasks"),
        Binding("3", "switch_tab('tab_stats')", "Stats"),
        Binding("c", "open_settings", "Settings"),
        Binding("h,question_mark", "open_help", "Help"),
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
                        "[dim][Space] Start/Pause  [s] Skip  [r] Reset  [+/-] Time  [a] Add Task  [t] Tasks  [c] Settings  [h/?] Help  [q] Quit[/dim]",
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

    def _write_terminal(self, text: str) -> None:
        """Low-level terminal writer through Textual's driver."""
        if not self.is_headless and self._driver is not None:
            try:
                self._driver.write(text)
            except Exception:
                pass

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

        # Ring console bell via Textual driver and send OSC escape sequences
        self.bell()
        self.notifications.notify_session_complete(
            finished_type,
            next_type,
            terminal_write=self._write_terminal,
        )

        if finished_type == SessionType.WORK:
            self.notify(
                f"Completed focus session! Take a {next_type.display_name.lower()}.",
                title="Focus Complete! 🍅",
                severity="information",
                timeout=10,
            )
        else:
            self.notify(
                "Break over! Ready for next focus session.",
                title="Break Finished ☕",
                severity="information",
                timeout=10,
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
        self.set_focus(None)
        tabs = self.query_one("#main_tabs", TabbedContent)
        tabs.active = tab_id
        if tab_id == "tab_tasks":
            task_widget = self.query_one("#task_list_widget", TaskListWidget)
            task_widget.refresh_tasks()
            task_widget.focus_input()
        elif tab_id == "tab_stats":
            self.query_one("#stats_widget", StatsWidget).refresh_stats()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Invoked when user clicks or activates a tab pane."""
        pane_id = getattr(event.pane, "id", None)
        if pane_id == "tab_tasks":
            try:
                task_widget = self.query_one("#task_list_widget", TaskListWidget)
                task_widget.refresh_tasks()
                task_widget.focus_input()
            except Exception:
                pass
        elif pane_id == "tab_stats":
            try:
                self.query_one("#stats_widget", StatsWidget).refresh_stats()
            except Exception:
                pass

    def action_open_add_task(self) -> None:
        """Open quick modal to create and optionally activate a task."""
        def handle_add_task_result(result: Optional[Tuple[Task, bool]]) -> None:
            if result is not None:
                task_obj, set_active = result
                saved_task = self.storage.add_task(task_obj.title, task_obj.pomodoros_estimated)
                if set_active:
                    self.storage.set_active_task_id(saved_task.id)
                    self.notify(f"Activated: {saved_task.title} 🍅", title="Task Active")
                else:
                    self.notify(f"Added: {saved_task.title}", title="Task Added")

                try:
                    self.query_one("#task_list_widget", TaskListWidget).refresh_tasks()
                except Exception:
                    pass
                self._update_all_displays()

        self.push_screen(AddTaskModal(), handle_add_task_result)

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
