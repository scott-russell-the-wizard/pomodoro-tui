"""Tests for PomodoroTimer logic."""

from pomodoro_tui.models import PomodoroSettings, SessionType, TimerStatus
from pomodoro_tui.timer import PomodoroTimer


def test_initial_timer_state():
    settings = PomodoroSettings(work_minutes=25, short_break_minutes=5)
    timer = PomodoroTimer(settings)
    assert timer.current_type == SessionType.WORK
    assert timer.status == TimerStatus.STOPPED
    assert timer.remaining_seconds == 25 * 60
    assert timer.total_seconds == 25 * 60
    assert timer.formatted_time == "25:00"
    assert timer.progress_fraction == 0.0


def test_timer_start_pause_toggle():
    timer = PomodoroTimer(PomodoroSettings(work_minutes=25))
    timer.start()
    assert timer.status == TimerStatus.RUNNING

    timer.pause()
    assert timer.status == TimerStatus.PAUSED

    timer.toggle()
    assert timer.status == TimerStatus.RUNNING

    timer.toggle()
    assert timer.status == TimerStatus.PAUSED


def test_timer_tick_and_countdown():
    timer = PomodoroTimer(PomodoroSettings(work_minutes=1))
    timer.start()
    initial_secs = timer.remaining_seconds
    done = timer.tick()
    assert not done
    assert timer.remaining_seconds == initial_secs - 1


def test_timer_advance_to_short_break():
    timer = PomodoroTimer(PomodoroSettings(work_minutes=25, short_break_minutes=5, long_break_interval=4))
    finished, next_s = timer.advance_session(was_completed=True)
    assert finished == SessionType.WORK
    assert next_s == SessionType.SHORT_BREAK
    assert timer.completed_work_sessions == 1
    assert timer.remaining_seconds == 5 * 60


def test_timer_advance_to_long_break():
    timer = PomodoroTimer(PomodoroSettings(work_minutes=25, short_break_minutes=5, long_break_minutes=15, long_break_interval=4))
    # 3 sessions completed -> short breaks
    for _ in range(3):
        timer.advance_session(was_completed=True) # -> short break
        timer.advance_session(was_completed=True) # -> work

    # 4th session completed -> long break
    finished, next_s = timer.advance_session(was_completed=True)
    assert finished == SessionType.WORK
    assert next_s == SessionType.LONG_BREAK
    assert timer.completed_work_sessions == 4
    assert timer.remaining_seconds == 15 * 60


def test_timer_adjust_time_while_stopped():
    timer = PomodoroTimer(PomodoroSettings(work_minutes=10))
    assert timer.status == TimerStatus.STOPPED
    assert timer.progress_fraction == 0.0

    # Increase 1 minute: remaining and total both 11m, progress stays 0%
    timer.adjust_time(60)
    assert timer.remaining_seconds == 11 * 60
    assert timer.total_seconds == 11 * 60
    assert timer.progress_fraction == 0.0

    # Decrease 2 minutes: remaining and total both 9m, progress stays 0%
    timer.adjust_time(-120)
    assert timer.remaining_seconds == 9 * 60
    assert timer.total_seconds == 9 * 60
    assert timer.progress_fraction == 0.0


def test_timer_adjust_time_while_running():
    timer = PomodoroTimer(PomodoroSettings(work_minutes=10))
    timer.start()
    # Simulate 2 minutes of work (120 seconds)
    for _ in range(120):
        timer.tick()
    assert timer.remaining_seconds == 8 * 60
    assert timer.total_seconds == 10 * 60
    # 2m elapsed of 10m = 20%
    assert abs(timer.progress_fraction - 0.20) < 0.01

    # Add 5 minutes: remaining is 13m, total becomes 15m, elapsed is still 2m
    timer.adjust_time(300)
    assert timer.remaining_seconds == 13 * 60
    assert timer.total_seconds == 15 * 60
    # 2m elapsed of 15m = 13.3%
    assert abs(timer.progress_fraction - (120 / 900)) < 0.01


def test_timer_reset():
    timer = PomodoroTimer(PomodoroSettings(work_minutes=25))
    timer.start()
    timer.tick()
    timer.tick()
    timer.reset()
    assert timer.status == TimerStatus.STOPPED
    assert timer.remaining_seconds == 25 * 60
