"""
Help and keyboard shortcuts modal screen.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class HelpModal(ModalScreen[None]):
    """Modal dialog displaying shortcut keys and Pomodoro guide."""

    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #help_dialog {
        width: 70;
        height: auto;
        max-height: 85%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #help_title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .help_section_title {
        text-style: bold;
        color: $warning;
        margin-top: 1;
        margin-bottom: 0;
    }

    .help_row {
        height: 1;
        margin-bottom: 0;
    }

    #btn_close_help {
        margin-top: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="help_dialog"):
            yield Static("🍅 Pomodoro TUI Help & Shortcuts", id="help_title")

            yield Static("Keyboard Shortcuts", classes="help_section_title")
            yield Static("  [bold]Space[/bold]        Start / Pause / Resume timer")
            yield Static("  [bold]s[/bold]            Skip current interval")
            yield Static("  [bold]r[/bold]            Reset current interval")
            yield Static("  [bold]+[/bold] / [bold]=[/bold]        Add 1 minute to timer")
            yield Static("  [bold]-[/bold]            Subtract 1 minute from timer")
            yield Static("  [bold]1[/bold]            Switch to Timer tab")
            yield Static("  [bold]2[/bold] or [bold]t[/bold]        Switch to Tasks tab")
            yield Static("  [bold]3[/bold]            Switch to Stats tab")
            yield Static("  [bold]c[/bold]            Open Settings dialog")
            yield Static("  [bold]h[/bold] or [bold]?[/bold]        Open this Help dialog")
            yield Static("  [bold]q[/bold]            Quit Pomodoro TUI")

            yield Static("The Pomodoro Technique", classes="help_section_title")
            yield Static("  1. Decide on the task to be done.")
            yield Static("  2. Set the timer to 25 minutes and focus completely.")
            yield Static("  3. When the timer rings, take a 5-minute short break.")
            yield Static("  4. After 4 focus sessions, take a longer 15-30 minute break.")

            yield Button("Close (Esc)", variant="primary", id="btn_close_help")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_close_help":
            self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()
