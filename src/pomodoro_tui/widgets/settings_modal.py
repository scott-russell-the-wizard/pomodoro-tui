"""
Settings modal dialog for configuring Pomodoro durations and preferences.
"""

from __future__ import annotations

from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, Switch

from pomodoro_tui.models import PomodoroSettings


class SettingsModal(ModalScreen[Optional[PomodoroSettings]]):
    """Modal dialog allowing configuration of Pomodoro settings."""

    DEFAULT_CSS = """
    SettingsModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #settings_dialog {
        width: 72;
        height: auto;
        max-height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #settings_title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .settings_grid {
        grid-size: 2;
        grid-gutter: 1;
        grid-columns: 1fr 1fr;
        height: auto;
    }

    .settings_field {
        height: auto;
        margin-bottom: 1;
    }

    .settings_label {
        color: $text-muted;
        margin-bottom: 0;
    }

    .switch_row {
        height: 3;
        align-vertical: middle;
        margin-bottom: 0;
    }

    .switch_label {
        width: 1fr;
        padding-top: 1;
    }

    #settings_buttons {
        margin-top: 1;
        align: right middle;
        height: auto;
    }

    #btn_save {
        margin-right: 1;
    }
    """

    def __init__(self, current_settings: PomodoroSettings) -> None:
        super().__init__()
        self.settings = current_settings

    def compose(self) -> ComposeResult:
        with Container(id="settings_dialog"):
            yield Static("⚙️ Pomodoro Settings", id="settings_title")

            with Grid(classes="settings_grid"):
                with Vertical(classes="settings_field"):
                    yield Label("Focus Duration (min):", classes="settings_label")
                    yield Input(str(self.settings.work_minutes), id="input_work", type="integer")

                with Vertical(classes="settings_field"):
                    yield Label("Short Break (min):", classes="settings_label")
                    yield Input(str(self.settings.short_break_minutes), id="input_short_break", type="integer")

                with Vertical(classes="settings_field"):
                    yield Label("Long Break (min):", classes="settings_label")
                    yield Input(str(self.settings.long_break_minutes), id="input_long_break", type="integer")

                with Vertical(classes="settings_field"):
                    yield Label("Long Break Interval (sessions):", classes="settings_label")
                    yield Input(str(self.settings.long_break_interval), id="input_interval", type="integer")

                with Vertical(classes="settings_field"):
                    yield Label("Daily Goal (sessions):", classes="settings_label")
                    yield Input(str(self.settings.daily_goal), id="input_goal", type="integer")

            with Vertical():
                with Horizontal(classes="switch_row"):
                    yield Label("Audio Bell Alert:", classes="switch_label")
                    yield Switch(value=self.settings.sound_enabled, id="switch_sound")

                with Horizontal(classes="switch_row"):
                    yield Label("Desktop Notifications:", classes="switch_label")
                    yield Switch(value=self.settings.desktop_notify, id="switch_desktop")

                with Horizontal(classes="switch_row"):
                    yield Label("Auto-start Breaks:", classes="switch_label")
                    yield Switch(value=self.settings.auto_start_breaks, id="switch_auto_breaks")

                with Horizontal(classes="switch_row"):
                    yield Label("Auto-start Work Sessions:", classes="switch_label")
                    yield Switch(value=self.settings.auto_start_work, id="switch_auto_work")

            with Horizontal(id="settings_buttons"):
                yield Button("Save", variant="success", id="btn_save")
                yield Button("Cancel", variant="default", id="btn_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_save":
            self._save_and_dismiss()
        elif event.button.id == "btn_cancel":
            self.dismiss(None)

    def _save_and_dismiss(self) -> None:
        try:
            work = int(self.query_one("#input_work", Input).value)
            short_b = int(self.query_one("#input_short_break", Input).value)
            long_b = int(self.query_one("#input_long_break", Input).value)
            interval = int(self.query_one("#input_interval", Input).value)
            goal = int(self.query_one("#input_goal", Input).value)
        except ValueError:
            return

        sound = self.query_one("#switch_sound", Switch).value
        desktop = self.query_one("#switch_desktop", Switch).value
        auto_breaks = self.query_one("#switch_auto_breaks", Switch).value
        auto_work = self.query_one("#switch_auto_work", Switch).value

        new_settings = PomodoroSettings(
            work_minutes=max(1, work),
            short_break_minutes=max(1, short_b),
            long_break_minutes=max(1, long_b),
            long_break_interval=max(1, interval),
            daily_goal=max(1, goal),
            sound_enabled=sound,
            desktop_notify=desktop,
            auto_start_breaks=auto_breaks,
            auto_start_work=auto_work,
        )
        self.dismiss(new_settings)

    def key_escape(self) -> None:
        self.dismiss(None)
