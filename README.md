# Pomodoro TUI 🍅

A modern, keyboard-driven Terminal User Interface (TUI) Pomodoro Timer built with Python and [Textual](https://textual.textualize.io/). Designed for deep focus, flow state tracking, and streamlined task management directly in your terminal.

---

## Features

- **Visual Digital Timer**: High-visibility block clock display (`MM:SS`) using Textual's scalable `Digits` widget.
- **Dynamic Session Phases**:
  - 🍅 **Focus Sessions**: Deep work intervals (default: 25 min).
  - ☕ **Short Breaks**: Quick recovery breaks (default: 5 min).
  - 🌴 **Long Breaks**: Extended recovery after every cycle (default: 15 min every 4 sessions).
- **Cycle & Streak Tracking**: Live cycle counter and cycle dots indicator (e.g. `[● ● ○ ○]`).
- **Interactive Task Management**:
  - Create and estimate tasks in pomodoros (e.g. `2 / 4 🍅`).
  - Set active task directly linked to the current countdown session.
  - Automatically increments completed pomodoros upon session completion.
  - Mark tasks complete or delete when finished.
- **Daily Analytics & History**:
  - Live summary cards: Total focus time today, completed pomodoros, daily goal progress bar.
  - Complete history log recording timestamps, session types, durations, and linked tasks.
- **Audio & Desktop Notifications**:
  - Audible/visual terminal bell (`\a`).
  - Optional desktop notifications via Linux `notify-send`.
- **Customizable In-App & Persistent Settings**:
  - Configure session lengths, long break intervals, daily goals, auto-start toggles, and notification preferences via interactive modal (`c`) or `.env` / CLI flags.
  - Persisted locally in `~/.config/pomodoro-tui/data.json`.

---

## Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| **`Space`** | Start / Pause / Resume timer |
| **`s`** | Skip current interval |
| **`r`** | Reset current interval |
| **`+`** / **`=`** | Add 1 minute to remaining time |
| **`-`** | Subtract 1 minute from remaining time |
| **`1`** | Switch to Timer view |
| **`2`** or **`t`** | Switch to Tasks view |
| **`3`** | Switch to Stats & History view |
| **`c`** | Open Settings dialog |
| **`h`** or **`?`** | Open Help & shortcuts dialog |
| **`q`** | Quit application |

---

## Architecture Overview

```text
pomodoro-tui/
├── pyproject.toml              # Packaging and dependency declarations
├── requirements.txt            # Pinned runtime and development dependencies
├── .env.example                # Sample environment configuration
├── src/
│   └── pomodoro_tui/
│       ├── __init__.py         # Package metadata
│       ├── __main__.py         # Entry point & CLI argument orchestration
│       ├── app.py              # Main Textual App class & layout engine
│       ├── config.py           # CLI argument parsing and environment loading
│       ├── models.py           # Dataclasses & enums (SessionType, Task, DailyStats, Settings)
│       ├── notifications.py    # Terminal bell & desktop notification dispatcher
│       ├── storage.py          # Atomic JSON persistence engine (~/.config/pomodoro-tui/data.json)
│       ├── timer.py            # Core state machine and countdown logic
│       ├── styles.tcss         # Textual CSS design system and color palette
│       └── widgets/
│           ├── __init__.py
│           ├── controls.py     # Action buttons and hotkey trigger row
│           ├── help_modal.py   # Modal cheatsheet and guide
│           ├── settings_modal.py # Modal form for tuning timer durations and toggles
│           ├── stats_view.py   # Daily analytics dashboard and history table
│           ├── task_list.py    # Task management and active task binding
│           └── timer_display.py # Big digital clock, progress bar, and badges
└── tests/
    ├── test_app.py             # Headless UI lifecycle and pilot integration tests
    ├── test_config.py          # CLI override unit tests
    ├── test_storage.py         # Persistence and stats calculation tests
    └── test_timer.py           # State machine transitions and countdown tests
```

---

## Prerequisites

- Python 3.10+
- Linux / macOS / BSD terminal with truecolor support

---

## Quickstart

### 1. Set Up Environment

```bash
# Clone or navigate to the repository
cd ~/projects/apps/pomodoro-tui

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies and editable CLI
pip install -e .
```

### 2. Launch the App

```bash
# Direct CLI command
pomodoro-tui

# Or run as a Python module
python3 -m pomodoro_tui
```

### 3. CLI Options

Customize session durations directly from the command line:

```bash
# 50-minute focus, 10-minute short break, 20-minute long break after 3 sessions:
pomodoro-tui --work 50 --short-break 10 --long-break 20 --interval 3

# Silent mode with desktop notifications enabled:
pomodoro-tui --no-sound --desktop-notify

# Specify custom persistent storage directory:
pomodoro-tui --data-dir ~/my-pomodoro-data
```

---

## Running Tests

The test suite includes unit tests for timer calculations and data persistence, along with asynchronous integration tests that exercise the UI and keyboard bindings in headless mode:

```bash
pytest
```

---

## License

MIT
