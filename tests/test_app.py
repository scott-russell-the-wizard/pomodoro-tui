"""Integration tests for PomodoroApp and UI workflows."""

import asyncio
from pathlib import Path
import tempfile
import pytest

from pomodoro_tui.app import PomodoroApp
from pomodoro_tui.models import SessionType, TimerStatus
from pomodoro_tui.widgets.help_modal import HelpModal
from pomodoro_tui.widgets.settings_modal import SettingsModal
from pomodoro_tui.widgets.task_list import TaskListWidget


def test_app_lifecycle_and_hotkeys():
    async def _test():
        with tempfile.TemporaryDirectory() as tmp_dir:
            app = PomodoroApp(data_dir=Path(tmp_dir))
            async with app.run_test() as pilot:
                await pilot.pause()
                assert app.timer.status == TimerStatus.STOPPED

                # Start
                await pilot.press("space")
                await pilot.pause()
                assert app.timer.status == TimerStatus.RUNNING

                # Pause
                await pilot.press("space")
                await pilot.pause()
                assert app.timer.status == TimerStatus.PAUSED

                # Time adjustments
                rem = app.timer.remaining_seconds
                await pilot.press("equal")
                await pilot.pause()
                assert app.timer.remaining_seconds == rem + 60

                await pilot.press("minus")
                await pilot.pause()
                assert app.timer.remaining_seconds == rem

                # Skip to short break
                await pilot.press("s")
                await pilot.pause()
                assert app.timer.current_type == SessionType.SHORT_BREAK

                # Reset
                await pilot.press("r")
                await pilot.pause()
                assert app.timer.status == TimerStatus.STOPPED

                # Tabs navigation
                await pilot.press("3")
                await pilot.pause()
                assert app.query_one("#main_tabs").active == "tab_stats"

                await pilot.press("1")
                await pilot.pause()
                assert app.query_one("#main_tabs").active == "tab_timer"

                await pilot.press("2")
                await pilot.pause()
                assert app.query_one("#main_tabs").active == "tab_tasks"

                # Switch back to timer tab via app action
                app.action_switch_tab("tab_timer")
                await pilot.pause()
                assert app.query_one("#main_tabs").active == "tab_timer"

                # Help screen
                await pilot.press("h")
                await pilot.pause()
                assert isinstance(app.screen, HelpModal)
                await pilot.press("escape")
                await pilot.pause()
                assert not isinstance(app.screen, HelpModal)

                # Settings screen
                await pilot.press("c")
                await pilot.pause()
                assert isinstance(app.screen, SettingsModal)
                await pilot.press("escape")
                await pilot.pause()
                assert not isinstance(app.screen, SettingsModal)

                # Quick Add Task modal
                await pilot.press("a")
                await pilot.pause()
                from pomodoro_tui.widgets.add_task_modal import AddTaskModal
                assert isinstance(app.screen, AddTaskModal)
                await pilot.press("escape")
                await pilot.pause()
                assert not isinstance(app.screen, AddTaskModal)

    asyncio.run(_test())


def test_app_task_linking_and_session_completion():
    async def _test():
        with tempfile.TemporaryDirectory() as tmp_dir:
            app = PomodoroApp(data_dir=Path(tmp_dir))
            async with app.run_test() as pilot:
                await pilot.pause()

                # Add a task via storage and set active
                task = app.storage.add_task("Finish documentation", pomodoros_estimated=2)
                app.storage.set_active_task_id(task.id)
                app._update_all_displays()
                await pilot.pause()

                active = app.storage.get_active_task()
                assert active is not None
                assert active.title == "Finish documentation"

                # Simulate session completion
                app._handle_session_finished()
                await pilot.pause()

                # Verify history was logged
                history = app.storage.get_history()
                assert len(history) == 1
                assert history[0].task_title == "Finish documentation"
                assert history[0].session_type == SessionType.WORK

                # Verify task progress incremented
                updated_task = app.storage.get_active_task()
                assert updated_task.pomodoros_completed == 1

                # Verify today stats updated
                stats = app.storage.get_today_stats()
                assert stats.completed_pomodoros == 1

    asyncio.run(_test())


def test_tables_geometry_and_visibility():
    async def _test():
        with tempfile.TemporaryDirectory() as tmp_dir:
            app = PomodoroApp(data_dir=Path(tmp_dir))
            async with app.run_test() as pilot:
                await pilot.pause()

                # Add a task so table has content
                app.storage.add_task("Test task visibility", pomodoros_estimated=3)

                # Switch to tasks tab
                app.action_switch_tab("tab_tasks")
                await pilot.pause()

                from textual.widgets import DataTable
                tasks_table = app.query_one("#tasks_table", DataTable)
                assert tasks_table.size.height > 0
                assert tasks_table.row_count == 1

                # Switch to stats tab
                app.action_switch_tab("tab_stats")
                await pilot.pause()

                stats_table = app.query_one("#history_table", DataTable)
                assert stats_table.size.height > 0

    asyncio.run(_test())
