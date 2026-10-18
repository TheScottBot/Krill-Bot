# Testing

Krill Bot targets Python 3.14. Install the development dependencies from the
repository root, then use these suites:

```powershell
.venv\Scripts\python.exe repository_checks.py
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
.venv\Scripts\mypy.exe krillbot repository_checks.py
.venv\Scripts\python.exe -m pytest
```

`repository_checks.py` enforces the typography rules and ownership of displayed
strings. `tests/test_repository_checks.py` enforces the portable-module import
boundary, package metadata, environment example, continuous integration gates,
and service hardening.

## Development-environment notes

The managed Windows sandbox cannot write to the temporary directory selected by
Python. Local reproduction in that sandbox sets `TEMP` and `TMP` to the ignored
`.sandbox-temp` directory while installing dependencies, and supplies a unique
directory below `.pytest_cache` as Pytest's base temporary directory. Neither
adjustment is required on a normal author machine or in continuous integration.

The available Python 3.14.7 Windows interpreter also failed to complete even an
`asyncio.sleep(0)` call in the managed execution environment. Command tests use
synchronous Discord doubles whose awaited methods never suspend, and complete
those immediate coroutines directly. Real event-loop behaviour remains an
author gate and will be exercised only with the development Discord bot.

## Author gates

No author gate has been cleared. The coding agent does not start Krill Bot with
a real Discord token. Live command registration, replies, daily posting,
forgetting, and removal behaviour require the author checks named by KE8.

