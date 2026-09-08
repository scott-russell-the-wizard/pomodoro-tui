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


def test_timer_adjust_time():
    timer = PomodoroTimer(PomodoroSettings(work_minutes=10))
    timer.adjust_time(60)
    assert timer.remaining_seconds == 11 * 60
    timer.adjust_time(-120)
    assert timer.remaining_seconds == 9 * 60


def test_timer_reset():
    timer = PomodoroTimer(PomodoroSettings(work_minutes=25))
    timer.start()
    timer.tick()
    timer.tick()
    timer.reset()
    assert timer.status == TimerStatus.STOPPED
    assert timer.remaining_seconds == 25 * 60
