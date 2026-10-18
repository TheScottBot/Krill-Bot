# Implementation deviations

## No aggregate format-change warning

Authorised by the author on 18 October 2026.

Specification draft 1 section 5.1 proposed counting refused pastes and warning
after an author-selected threshold of `not-a-result` outcomes with no successful
log. The author selected no aggregate refusal threshold or warning. Each
unrecognised paste instead receives private guidance to open an issue or
start a discussion on the Krill Bot repository if the bot seems out of date
(changed from contacting the author on Discord, at the author's request, on
18 October 2026). The submitted text remains unstored and absent from logs; a
privacy-safe server and reason diagnostic remains.

## Daily post table carries the reset time and optional times

Authorised by the author on 18 October 2026.

Specification draft 1 section 4.1 keeps ProcBot's `daily_posts` table
unchanged, with a required `clock`. The author chose a per-server reset time
and post time, each falling back to the environment file and then to 04:00 and
17:00. Schema version 2 therefore adds a `reset_clock` column and lets both
times be empty, so a server that chose none follows the fallback even after it
changes. The upgrade from version 1 keeps every row. Covering tests:
`test_version_one_database_upgrades_keeping_rows_and_allowing_default_times`
and the `tests/test_daily.py` fallback tests.

## A pure time module beside the specified layout

Specification draft 1 section 3.1 lists no `clock.py`. The time grammar is
needed by both `config.py` and `/setup daily`, and `daily.py` imports
`config`, so the grammar lives in its own pure module rather than in either,
which datum 0.7 requires to hold it once. The pure-import check covers it.
Covering tests: `tests/test_clock.py`.

