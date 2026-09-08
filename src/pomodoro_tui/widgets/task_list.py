"""
Task management widget allowing adding, completing, and linking tasks to Pomodoro sessions.
"""

from __future__ import annotations

from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, DataTable, Input, Label, Static

from pomodoro_tui.models import Task
from pomodoro_tui.storage import PomodoroStorage


class TaskListWidget(Widget):
    """Widget for managing and selecting tasks."""

    DEFAULT_CSS = """
    TaskListWidget {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    #task_header {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    #add_task_bar {
        height: auto;
        margin-bottom: 1;
    }

    #input_task_title {
        width: 1fr;
        margin-right: 1;
    }

    #input_task_est {
        width: 12;
        margin-right: 1;
    }

    #task_actions_bar {
        height: auto;
        margin-top: 1;
        align: center middle;
    }

    .task_action_btn {
        margin-right: 1;
    }

    #tasks_table {
        height: 1fr;
        border: solid $primary;
    }
    """

    class ActiveTaskChanged(Message):
        """Active task was changed."""
        def __init__(self, task: Optional[Task]) -> None:
            super().__init__()
            self.task = task

    def __init__(self, storage: PomodoroStorage, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.storage = storage

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("📋 Task Management", id="task_header")

            with Horizontal(id="add_task_bar"):
                yield Input(placeholder="What are you working on?", id="input_task_title")
                yield Input(placeholder="Est 🍅 (1-10)", id="input_task_est", type="integer")
                yield Button("➕ Add Task", variant="success", id="btn_add_task")

            yield DataTable(id="tasks_table", cursor_type="row")

            with Horizontal(id="task_actions_bar"):
                yield Button("🎯 Set Active", variant="primary", id="btn_set_active", classes="task_action_btn")
                yield Button("⚪ Clear Active", variant="default", id="btn_clear_active", classes="task_action_btn")
                yield Button("✓ Toggle Done", variant="warning", id="btn_toggle_done", classes="task_action_btn")
                yield Button("🗑 Delete", variant="error", id="btn_delete_task", classes="task_action_btn")

    def on_mount(self) -> None:
        table = self.query_one("#tasks_table", DataTable)
        table.add_column("Active", width=8)
        table.add_column("Status", width=10)
        table.add_column("Task Title", width=40)
        table.add_column("Progress", width=14)
        table.add_column("ID", width=10)
        self.refresh_tasks()

    def refresh_tasks(self) -> None:
        table = self.query_one("#tasks_table", DataTable)
        table.clear()
        tasks = self.storage.get_tasks()
        active_id = self.storage.get_active_task_id()

        for t in tasks:
            active_str = "⭐ ACTIVE" if t.id == active_id else ""
            status_str = "✓ Done" if t.is_completed else "○ Pending"
            progress_str = f"{t.pomodoros_completed} / {t.pomodoros_estimated} 🍅"
            table.add_row(active_str, status_str, t.title, progress_str, t.id, key=t.id)

    def _get_selected_task_id(self) -> Optional[str]:
        table = self.query_one("#tasks_table", DataTable)
        if table.row_count == 0 or table.cursor_row < 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        return str(row_key.value) if row_key else None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn_add_task":
            self._handle_add_task()
        elif button_id == "btn_set_active":
            self._handle_set_active()
        elif button_id == "btn_clear_active":
            self.storage.set_active_task_id(None)
            self.refresh_tasks()
            self.post_message(self.ActiveTaskChanged(None))
        elif button_id == "btn_toggle_done":
            self._handle_toggle_done()
        elif button_id == "btn_delete_task":
            self._handle_delete_task()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in ("input_task_title", "input_task_est"):
            self._handle_add_task()

    def _handle_add_task(self) -> None:
        title_input = self.query_one("#input_task_title", Input)
        est_input = self.query_one("#input_task_est", Input)

        title = title_input.value.strip()
        if not title:
            return

        try:
            est = int(est_input.value.strip()) if est_input.value.strip() else 1
            est = max(1, min(est, 50))
        except ValueError:
            est = 1

        new_task = self.storage.add_task(title=title, pomodoros_estimated=est)
        title_input.value = ""
        est_input.value = ""

        # If no active task currently, set this new task active
        if not self.storage.get_active_task_id():
            self.storage.set_active_task_id(new_task.id)
            self.post_message(self.ActiveTaskChanged(new_task))

        self.refresh_tasks()

    def _handle_set_active(self) -> None:
        task_id = self._get_selected_task_id()
        if not task_id:
            return
        self.storage.set_active_task_id(task_id)
        self.refresh_tasks()
        active_task = self.storage.get_active_task()
        self.post_message(self.ActiveTaskChanged(active_task))

    def _handle_toggle_done(self) -> None:
        task_id = self._get_selected_task_id()
        if not task_id:
            return
        tasks = self.storage.get_tasks()
        for t in tasks:
            if t.id == task_id:
                t.is_completed = not t.is_completed
                self.storage.update_task(t)
                break
        self.refresh_tasks()

    def _handle_delete_task(self) -> None:
        task_id = self._get_selected_task_id()
        if not task_id:
            return
        was_active = (self.storage.get_active_task_id() == task_id)
        self.storage.delete_task(task_id)
        if was_active:
            self.post_message(self.ActiveTaskChanged(None))
        self.refresh_tasks()
