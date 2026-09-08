"""Tests for CLI parsing and configuration loading."""

from pomodoro_tui.config import apply_cli_overrides, parse_cli_args
from pomodoro_tui.models import PomodoroSettings


def test_cli_overrides_durations():
    settings = PomodoroSettings()
    args = parse_cli_args(["--work", "50", "--short-break", "10", "--long-break", "20", "--interval", "3"])
    updated = apply_cli_overrides(settings, args)

    assert updated.work_minutes == 50
    assert updated.short_break_minutes == 10
    assert updated.long_break_minutes == 20
    assert updated.long_break_interval == 3


def test_cli_flags_toggles():
    settings = PomodoroSettings(sound_enabled=True)
    args = parse_cli_args(["--no-sound", "--desktop-notify", "--auto-breaks", "--auto-work", "--goal", "12"])
    updated = apply_cli_overrides(settings, args)

    assert not updated.sound_enabled
    assert updated.desktop_notify
    assert updated.auto_start_breaks
    assert updated.auto_start_work
    assert updated.daily_goal == 12
