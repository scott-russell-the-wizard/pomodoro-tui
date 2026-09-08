"""
Data models and enumerations for Pomodoro TUI.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class SessionType(str, Enum):
    """Pomodoro session types."""
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"

    @property
    def display_name(self) -> str:
        if self == SessionType.WORK:
            return "Focus Session"
        elif self == SessionType.SHORT_BREAK:
            return "Short Break"
        elif self == SessionType.LONG_BREAK:
            return "Long Break"
        return self.value

    @property
    def icon(self) -> str:
        if self == SessionType.WORK:
            return "🍅"
        elif self == SessionType.SHORT_BREAK:
            return "☕"
        elif self == SessionType.LONG_BREAK:
            return "🌴"
        return "⏱️"


class TimerStatus(str, Enum):
    """Timer state enumeration."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class PomodoroSettings:
    """Configurable user settings."""
    work_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    long_break_interval: int = 4
    daily_goal: int = 8
    sound_enabled: bool = True
    desktop_notify: bool = False
    auto_start_breaks: bool = False
    auto_start_work: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PomodoroSettings:
        valid_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class Task:
    """A task trackable with pomodoros."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    pomodoros_estimated: int = 1
    pomodoros_completed: int = 0
    is_completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Task:
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", ""),
            pomodoros_estimated=int(data.get("pomodoros_estimated", 1)),
            pomodoros_completed=int(data.get("pomodoros_completed", 0)),
            is_completed=bool(data.get("is_completed", False)),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


@dataclass
class CompletedSession:
    """Historical record of a completed pomodoro session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_type: SessionType = SessionType.WORK
    duration_seconds: int = 1500
    completed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    task_id: Optional[str] = None
    task_title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["session_type"] = self.session_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CompletedSession:
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            session_type=SessionType(data.get("session_type", "work")),
            duration_seconds=int(data.get("duration_seconds", 1500)),
            completed_at=data.get("completed_at", datetime.now().isoformat()),
            task_id=data.get("task_id"),
            task_title=data.get("task_title"),
        )


@dataclass
class DailyStats:
    """Aggregated statistics for a given day."""
    date_str: str = field(default_factory=lambda: date.today().isoformat())
    completed_pomodoros: int = 0
    total_focus_seconds: int = 0
    short_breaks_count: int = 0
    long_breaks_count: int = 0

    @property
    def formatted_focus_time(self) -> str:
        hours = self.total_focus_seconds // 3600
        minutes = (self.total_focus_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
