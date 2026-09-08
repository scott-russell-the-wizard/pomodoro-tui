"""
Quick Add Task modal dialog.
"""

from __future__ import annotations

from typing import Optional, Tuple
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, Switch

from pomodoro_tui.models import Task


class AddTaskModal(ModalScreen[Optional[Tuple[Task, bool]]]):
    """Modal dialog to quickly create and optionally activate a task."""

    DEFAULT_CSS = """
    AddTaskModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #add_task_dialog {
        width: 65;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #add_task_modal_title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .modal_field {
        margin-bottom: 1;
        height: auto;
    }

    .modal_label {
        color: $text-muted;
        margin-bottom: 0;
    }

    #modal_switch_row {
        height: 3;
        align-vertical: middle;
        margin-top: 1;
    }

    #modal_switch_label {
        width: 1fr;
        padding-top: 1;
    }

    #modal_buttons {
        margin-top: 1;
        align: right middle;
        height: auto;
    }

    #btn_confirm_add {
        margin-right: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="add_task_dialog"):
            yield Static("➕ Add New Task", id="add_task_modal_title")

            with Vertical(classes="modal_field"):
                yield Label("Task Title / Objective:", classes="modal_label")
                yield Input(placeholder="e.g. Refactor auth service", id="input_modal_task_title")

            with Vertical(classes="modal_field"):
                yield Label("Estimated Pomodoros (1-10 🍅):", classes="modal_label")
                yield Input("2", id="input_modal_task_est", type="integer")

            with Horizontal(id="modal_switch_row"):
                yield Label("Set as Active Task for Timer:", id="modal_switch_label")
                yield Switch(value=True, id="switch_modal_set_active")

            with Horizontal(id="modal_buttons"):
                yield Button("Add Task [Enter]", variant="success", id="btn_confirm_add")
                yield Button("Cancel [Esc]", variant="default", id="btn_cancel_add")

    def on_mount(self) -> None:
        self.query_one("#input_modal_task_title", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_confirm_add":
            self._submit()
        elif event.button.id == "btn_cancel_add":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        title_in = self.query_one("#input_modal_task_title", Input).value.strip()
        if not title_in:
            return

        est_in = self.query_one("#input_modal_task_est", Input).value.strip()
        try:
            est = int(est_in) if est_in else 1
            est = max(1, min(est, 50))
        except ValueError:
            est = 1

        set_active = self.query_one("#switch_modal_set_active", Switch).value
        task = Task(title=title_in, pomodoros_estimated=est)
        self.dismiss((task, set_active))

    def key_escape(self) -> None:
        self.dismiss(None)
