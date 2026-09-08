"""
Storage manager for persisting settings, tasks, and session logs in JSON format.
"""

from __future__ import annotations

from datetime import date, datetime
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from pomodoro_tui.models import (
    PomodoroSettings,
    Task,
    CompletedSession,
    DailyStats,
    SessionType,
)


class PomodoroStorage:
    """Manages file-based JSON persistence for Pomodoro TUI."""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        if data_dir is None:
            self.data_dir = Path.home() / ".config" / "pomodoro-tui"
        else:
            self.data_dir = Path(data_dir)

        self.file_path = self.data_dir / "data.json"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _load_raw(self) -> Dict[str, Any]:
        if not self.file_path.is_file():
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_raw(self, data: Dict[str, Any]) -> None:
        self._ensure_dir()
        temp_path = self.file_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_path.replace(self.file_path)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

    # Settings
    def load_settings(self, fallback: Optional[PomodoroSettings] = None) -> PomodoroSettings:
        raw = self._load_raw()
        settings_data = raw.get("settings")
        if settings_data and isinstance(settings_data, dict):
            return PomodoroSettings.from_dict(settings_data)
        return fallback or PomodoroSettings()

    def save_settings(self, settings: PomodoroSettings) -> None:
        raw = self._load_raw()
        raw["settings"] = settings.to_dict()
        self._save_raw(raw)

    # Tasks
    def get_tasks(self) -> List[Task]:
        raw = self._load_raw()
        tasks_data = raw.get("tasks", [])
        return [Task.from_dict(t) for t in tasks_data]

    def save_tasks(self, tasks: List[Task]) -> None:
        raw = self._load_raw()
        raw["tasks"] = [t.to_dict() for t in tasks]
        self._save_raw(raw)

    def add_task(self, title: str, pomodoros_estimated: int = 1) -> Task:
        tasks = self.get_tasks()
        task = Task(title=title, pomodoros_estimated=pomodoros_estimated)
        tasks.append(task)
        self.save_tasks(tasks)
        return task

    def update_task(self, task: Task) -> None:
        tasks = self.get_tasks()
        for idx, t in enumerate(tasks):
            if t.id == task.id:
                tasks[idx] = task
                break
        self.save_tasks(tasks)

    def delete_task(self, task_id: str) -> None:
        tasks = [t for t in self.get_tasks() if t.id != task_id]
        self.save_tasks(tasks)
        # If deleted was active, clear active
        if self.get_active_task_id() == task_id:
            self.set_active_task_id(None)

    def get_active_task_id(self) -> Optional[str]:
        raw = self._load_raw()
        return raw.get("active_task_id")

    def set_active_task_id(self, task_id: Optional[str]) -> None:
        raw = self._load_raw()
        raw["active_task_id"] = task_id
        self._save_raw(raw)

    def get_active_task(self) -> Optional[Task]:
        task_id = self.get_active_task_id()
        if not task_id:
            return None
        for t in self.get_tasks():
            if t.id == task_id:
                return t
        return None

    # History and sessions
    def log_session(self, session: CompletedSession) -> None:
        raw = self._load_raw()
        history = raw.get("history", [])
        history.append(session.to_dict())
        raw["history"] = history
        self._save_raw(raw)

    def get_history(self, limit: int = 100) -> List[CompletedSession]:
        raw = self._load_raw()
        history_data = raw.get("history", [])
        sessions = [CompletedSession.from_dict(s) for s in history_data]
        sessions.sort(key=lambda s: s.completed_at, reverse=True)
        return sessions[:limit]

    def get_today_stats(self) -> DailyStats:
        today_iso = date.today().isoformat()
        sessions = self.get_history(limit=500)
        stats = DailyStats(date_str=today_iso)

        for s in sessions:
            if s.completed_at.startswith(today_iso):
                if s.session_type == SessionType.WORK:
                    stats.completed_pomodoros += 1
                    stats.total_focus_seconds += s.duration_seconds
                elif s.session_type == SessionType.SHORT_BREAK:
                    stats.short_breaks_count += 1
                elif s.session_type == SessionType.LONG_BREAK:
                    stats.long_breaks_count += 1

        return stats
