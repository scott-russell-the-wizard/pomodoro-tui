"""
Configuration management and CLI argument parser for Pomodoro TUI.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional

from pomodoro_tui.models import PomodoroSettings


def load_env_file(path: Optional[Path] = None) -> None:
    """Simple parser to load .env key-values into os.environ if present."""
    if path is None:
        path = Path(".env")
    if not path.is_file():
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


def get_settings_from_env() -> PomodoroSettings:
    """Build PomodoroSettings overridden by environment variables."""
    load_env_file()

    def get_int(key: str, default: int) -> int:
        val = os.environ.get(key)
        if val is not None:
            try:
                return int(val)
            except ValueError:
                pass
        return default

    def get_bool(key: str, default: bool) -> bool:
        val = os.environ.get(key)
        if val is not None:
            return val.lower() in ("1", "true", "yes", "on")
        return default

    return PomodoroSettings(
        work_minutes=get_int("POMODORO_WORK_MINUTES", 25),
        short_break_minutes=get_int("POMODORO_SHORT_BREAK_MINUTES", 5),
        long_break_minutes=get_int("POMODORO_LONG_BREAK_MINUTES", 15),
        long_break_interval=get_int("POMODORO_LONG_BREAK_INTERVAL", 4),
        daily_goal=get_int("POMODORO_DAILY_GOAL", 8),
        sound_enabled=get_bool("POMODORO_SOUND_ENABLED", True),
        desktop_notify=get_bool("POMODORO_DESKTOP_NOTIFY", False),
        auto_start_breaks=get_bool("POMODORO_AUTO_START_BREAKS", False),
        auto_start_work=get_bool("POMODORO_AUTO_START_WORK", False),
    )


def parse_cli_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command line arguments for the pomodoro app."""
    parser = argparse.ArgumentParser(
        prog="pomodoro-tui",
        description="A modern, feature-rich Terminal User Interface Pomodoro Timer.",
    )
    parser.add_argument(
        "-w", "--work",
        type=int,
        dest="work_minutes",
        help="Focus session duration in minutes (default: 25)",
    )
    parser.add_argument(
        "-s", "--short-break",
        type=int,
        dest="short_break_minutes",
        help="Short break duration in minutes (default: 5)",
    )
    parser.add_argument(
        "-l", "--long-break",
        type=int,
        dest="long_break_minutes",
        help="Long break duration in minutes (default: 15)",
    )
    parser.add_argument(
        "-i", "--interval",
        type=int,
        dest="long_break_interval",
        help="Number of focus sessions before long break (default: 4)",
    )
    parser.add_argument(
        "-g", "--goal",
        type=int,
        dest="daily_goal",
        help="Daily completed pomodoros goal (default: 8)",
    )
    parser.add_argument(
        "--no-sound",
        action="store_true",
        dest="no_sound",
        help="Disable terminal bell audio alert",
    )
    parser.add_argument(
        "--desktop-notify",
        action="store_true",
        dest="desktop_notify",
        help="Enable desktop notification popups",
    )
    parser.add_argument(
        "--auto-breaks",
        action="store_true",
        dest="auto_start_breaks",
        help="Automatically start breaks without waiting for user input",
    )
    parser.add_argument(
        "--auto-work",
        action="store_true",
        dest="auto_start_work",
        help="Automatically start next focus session when break completes",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        dest="data_dir",
        help="Directory to store persistent data (default: ~/.config/pomodoro-tui)",
    )
    return parser.parse_args(args)


def apply_cli_overrides(settings: PomodoroSettings, ns: argparse.Namespace) -> PomodoroSettings:
    """Override settings with CLI flags where provided."""
    if ns.work_minutes is not None:
        settings.work_minutes = ns.work_minutes
    if ns.short_break_minutes is not None:
        settings.short_break_minutes = ns.short_break_minutes
    if ns.long_break_minutes is not None:
        settings.long_break_minutes = ns.long_break_minutes
    if ns.long_break_interval is not None:
        settings.long_break_interval = ns.long_break_interval
    if ns.daily_goal is not None:
        settings.daily_goal = ns.daily_goal
    if ns.no_sound:
        settings.sound_enabled = False
    if ns.desktop_notify:
        settings.desktop_notify = True
    if ns.auto_start_breaks:
        settings.auto_start_breaks = True
    if ns.auto_start_work:
        settings.auto_start_work = True
    return settings
