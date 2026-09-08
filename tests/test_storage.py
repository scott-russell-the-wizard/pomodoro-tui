"""Tests for PomodoroStorage and models."""

from pathlib import Path
from pomodoro_tui.models import PomodoroSettings, SessionType, CompletedSession
from pomodoro_tui.storage import PomodoroStorage


def test_storage_tasks(tmp_path: Path):
    storage = PomodoroStorage(data_dir=tmp_path)
    assert storage.get_tasks() == []

    task = storage.add_task("Write docs", pomodoros_estimated=3)
    assert task.title == "Write docs"
    assert task.pomodoros_estimated == 3

    tasks = storage.get_tasks()
    assert len(tasks) == 1
    assert tasks[0].id == task.id

    storage.set_active_task_id(task.id)
    active = storage.get_active_task()
    assert active is not None
    assert active.title == "Write docs"

    storage.delete_task(task.id)
    assert len(storage.get_tasks()) == 0
    assert storage.get_active_task() is None


def test_storage_settings(tmp_path: Path):
    storage = PomodoroStorage(data_dir=tmp_path)
    custom_settings = PomodoroSettings(work_minutes=50, short_break_minutes=10)
    storage.save_settings(custom_settings)

    loaded = storage.load_settings()
    assert loaded.work_minutes == 50
    assert loaded.short_break_minutes == 10


def test_storage_stats_calculation(tmp_path: Path):
    storage = PomodoroStorage(data_dir=tmp_path)
    session1 = CompletedSession(
        session_type=SessionType.WORK,
        duration_seconds=1500,
        task_title="Coding",
    )
    session2 = CompletedSession(
        session_type=SessionType.SHORT_BREAK,
        duration_seconds=300,
    )
    storage.log_session(session1)
    storage.log_session(session2)

    stats = storage.get_today_stats()
    assert stats.completed_pomodoros == 1
    assert stats.total_focus_seconds == 1500
    assert stats.short_breaks_count == 1
