"""
Action buttons for controlling the Pomodoro timer.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button

from pomodoro_tui.models import TimerStatus


class TimerControls(Widget):
    """Horizontal bar containing interactive timer action buttons."""

    DEFAULT_CSS = """
    TimerControls {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
        margin-bottom: 1;
    }

    .control_btn {
        margin-left: 1;
        margin-right: 1;
        min-width: 12;
    }

    #btn_toggle {
        min-width: 18;
    }
    """

    class ToggleRequested(Message):
        """Requested to start or pause."""

    class SkipRequested(Message):
        """Requested to skip session."""

    class ResetRequested(Message):
        """Requested to reset session."""

    class AdjustTimeRequested(Message):
        """Requested to add or subtract time."""
        def __init__(self, delta_seconds: int) -> None:
            super().__init__()
            self.delta_seconds = delta_seconds

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("▶ Start [Space]", variant="success", id="btn_toggle", classes="control_btn")
            yield Button("⏭ Skip [s]", variant="default", id="btn_skip", classes="control_btn")
            yield Button("↺ Reset [r]", variant="error", id="btn_reset", classes="control_btn")
            yield Button("-1m", variant="default", id="btn_sub_1m", classes="control_btn")
            yield Button("+1m", variant="default", id="btn_add_1m", classes="control_btn")
            yield Button("+5m", variant="default", id="btn_add_5m", classes="control_btn")

    def update_status(self, status: TimerStatus) -> None:
        """Update toggle button label and variant based on timer status."""
        btn = self.query_one("#btn_toggle", Button)
        if status == TimerStatus.RUNNING:
            btn.label = "⏸ Pause [Space]"
            btn.variant = "warning"
        else:
            btn.label = "▶ Start [Space]"
            btn.variant = "success"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn_toggle":
            self.post_message(self.ToggleRequested())
        elif button_id == "btn_skip":
            self.post_message(self.SkipRequested())
        elif button_id == "btn_reset":
            self.post_message(self.ResetRequested())
        elif button_id == "btn_sub_1m":
            self.post_message(self.AdjustTimeRequested(-60))
        elif button_id == "btn_add_1m":
            self.post_message(self.AdjustTimeRequested(60))
        elif button_id == "btn_add_5m":
            self.post_message(self.AdjustTimeRequested(300))
