# Testing

Krill Bot targets Python 3.14. Install the development dependencies from the
repository root, then use these suites:

```powershell
.venv\Scripts\python.exe repository_checks.py
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
.venv\Scripts\mypy.exe krillbot repository_checks.py
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -X dev -m pytest -W error
```

`repository_checks.py` enforces the typography rules and ownership of displayed
strings. `tests/test_repository_checks.py` enforces the portable-module import
boundary, package metadata, environment example, continuous integration gates,
and service hardening.

## Memory and undefined behaviour analysis

Datum 0.10 asks for the parser to run under whatever memory and undefined
behaviour analysis the language provides. Krill Bot is pure Python with no
extension modules of its own, so the language manages memory and has no
undefined behaviour that a sanitiser could find in this code.

What CPython does offer is development mode, read from the Python 3.14
documentation on 18 October 2026. `-X dev` installs the memory allocator debug
hooks, which detect buffer underflow and overflow, allocator API violations,
and unsafe use of the global interpreter lock; enables faulthandler for crash
tracebacks; shows `ResourceWarning` and deprecation warnings; and checks
`encoding` and `errors` arguments eagerly. It is not a substitute for
AddressSanitizer or UndefinedBehaviorSanitizer, which would require a
sanitiser build of CPython itself and would examine the interpreter and its
third-party extension modules rather than Krill Bot.

Continuous integration therefore runs the whole suite, parser properties
included, with `python -X dev -m pytest -W error`, so any resource left open
fails the run. The gate was proven on 18 October 2026 against a planted test
that leaked an unclosed SQLite connection: plain Pytest passed it, and the gate
command failed it with `ResourceWarning`.

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

