# Testing

Krill Bot targets Python 3.14. Install the development dependencies from the
repository root, then use these suites:

```powershell
.venv\Scripts\python.exe repository_checks.py
.venv\Scripts\python.exe site_builder.py --check
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
.venv\Scripts\mypy.exe krillbot repository_checks.py site_builder.py
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -X dev -m pytest -W error
```

`repository_checks.py` enforces the typography rules and ownership of displayed
strings. `site_builder.py --check` fails when `docs/privacy.html` or
`docs/terms.html` differs from `PRIVACY.md` or `TERMS.md`; after editing either
record, run `.venv\Scripts\python.exe site_builder.py` to rebuild the pages. `tests/test_repository_checks.py` enforces the portable-module import
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

For the same reason, the `/dive forget` button tests call each button's
callback and the view's interaction check directly. A view built without an
event loop has no stop future, so whether it reports itself finished is not
asserted; the tests assert that the buttons are removed from the message.

## Author gates

The coding agent does not start Krill Bot with a real Discord token; every
check below was run by the author against the development bot.

### KE8, 18 October 2026

The agent listed five checks for the development bot in a test server:

1. logging with `/dive log` and with the Log Krillion result menu, and the
   menu refusing someone else's message
2. `/dive today` hiding scores until the viewer has logged, then showing them,
   with `/dive board period:week` and `/dive streak`
3. a daily post set a few minutes ahead with `/setup daily here`, showing
   yesterday's board and pinging nobody
4. `/dive forget scope:here`, with Delete working for the caller and the
   buttons refusing a second account
5. removing the bot from the test server and its rows leaving the development
   database

The author reported, in their own words: "Yup each of those are good and work.
Saves remembers, deletes all good". That statement is the only evidence for
these gates. It did not record the commit, the test server, the times
observed, or each check's outcome separately. When it was given, the
repository was at commit `0de6887` with no code changes outstanding, which
suggests but does not prove that the checks ran against that commit.

On 18 October 2026, after KE7, the author reported in their own words: "All
green on tests". The report did not record the machine, Python version or which
of the suites above were run, so it is recorded as the author's statement that
the automated tests passed, not as a reproduction of every suite on a clean
machine.

