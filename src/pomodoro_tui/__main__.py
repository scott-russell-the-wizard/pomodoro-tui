"""
Entry point for pomodoro-tui CLI execution.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pomodoro_tui.app import PomodoroApp
from pomodoro_tui.config import apply_cli_overrides, get_settings_from_env, parse_cli_args


def main() -> None:
    """Main execution function."""
    args = parse_cli_args(sys.argv[1:])

    # Load defaults / environment
    settings = get_settings_from_env()

    # Apply CLI overrides
    settings = apply_cli_overrides(settings, args)

    data_dir = Path(args.data_dir) if args.data_dir else None

    app = PomodoroApp(settings=settings, data_dir=data_dir)
    app.run()


if __name__ == "__main__":
    main()
