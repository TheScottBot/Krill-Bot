# Actual contract evaluation

Plan-stage evidence for the Krillion Discord bot specification. This record is
append-only history for observations and experiments. Present-tense conclusions
may be revised by a dated note when later evidence changes them.

## Evaluation context

- Evaluation date: 18 October 2026.
- Engineering datum: version 2, dated 20 September 2026.
- Project specification: draft 1, dated 18 October 2026.
- Development platform: Windows, with the repository at
  `C:\Users\sptip\Documents\GitHub\KrillionBot`.
- Repository state when planning began: an empty Git repository on `main`, with
  no commits and no working files.
- Optional datum modules: module A does not apply because the implementation is
  Python; module B does not apply because this repository holds one product.

No implementation code or behavioural tests had been written when this record
was created.

## Source inventory

### Project specification

Source: `C:\Users\sptip\Downloads\krillion-discord-bot-spec.md`.

Observed: the file identifies itself as draft 1, dated 18 October 2026, and
applies engineering datum version 2. It defines phases KE1 through KE8,
decisions KD1 through KD9, and unverified values KU1 through KU12.

Conclusion: the Plan stage blocks KE1 until KD2 and KD7 are settled. Further
decisions and unverified values block the later phases named by the
specification.

### Engineering datum

Source: `C:\Users\sptip\Documents\GitHub\ENGINEERING_DATUM.md`.

Observed: version 2, dated 20 September 2026. It requires source evidence,
author-owned decisions, test-first implementation, reproduction reports, and
strict separation between automated criteria and author gates. It permanently
prohibits every Git write operation by the agent.

Conclusion: planning records and documentation may be written now.
Implementation and behavioural tests may not begin until the Plan stage has
settled the phase concerned.

## Reference repositories

The following local repositories existed when checked on 18 October 2026.
Repository contents are read as source; no Git write operation is permitted.

| Reference | Recorded origin | Local revision | Initial observation |
|---|---|---|---|
| ProcBot | `https://github.com/TheScottBot/ProcBot.git` | `2c7ac2da2f0af1da780075dc2e671f3af3848d78` | Matches the revision named by the specification. |
| Hammered of Witches | `https://github.com/TheScottBot/Hammered-of-Witches.git` | `a6c3db1e7c5ff9c60a5d4ec3e373ca70decc8b70` | Matches the revision named by the specification. |
| ktdi | `https://github.com/TheScottBot/ktdi.git` | `dbefaf671b0937db6d9e9ad3dd862f3f1c707103` | Matches the revision named by the specification. |
| FtrIO | `https://github.com/TheScottBot/FtrIO.git` | `2224bc9e71065e4dc13d4d20817e0aaf530fad8b` | Does not match the `FtrOnOff/FtrIO` path named by the datum. It cannot silently substitute for that reference. |
| ftrio-python | `https://github.com/FtrOnOff/ftrio-python.git` | `b95ec4e1feaf1b3c74a30a43edd5e03c90f7ad68` | The origin path matches the datum. |
| ftrio-rust | `https://github.com/FtrOnOff/ftrio-rust.git` | `e814d40758eb3524d64e9e40688bb8c59de65989` | The origin path matches the datum. |

The local sandbox permits direct reading of reference files but does not permit
Git to change into these sibling repositories. This affects inspection method,
not the target repository.

## ProcBot observations

Source revision: `2c7ac2da2f0af1da780075dc2e671f3af3848d78`.
Files read on 18 October 2026: `AGENTS.md`, `README.md`, `pyproject.toml`,
`procbot/bot.py`, `procbot/config.py`, `procbot/daily.py`, `procbot/db.py`,
`tests/conftest.py`, and `tests/fakes.py`.

Observed:

- The project requires Python 3.10 or later and declares `discord.py>=2.4`,
  `python-dotenv>=1.0`, and `tzdata>=2024.1`.
- It uses `discord.Client`, `app_commands.CommandTree`, and default intents.
- Its command completion log records the server and command, not the user or
  submitted search text.
- Its tests disable dotenv loading before importing the package and use an
  in-memory SQLite connection.
- Its daily loop checks once per minute, stores the next run in UTC, skips a
  post after a six-hour grace period, and advances the schedule in a `finally`
  block after a posting attempt.
- It has no `LICENSE` file at this revision.

Conclusion: the architectural observations cited by the bot specification are
supported by the files inspected. KD7 is not answerable as written because
there is no ProcBot licence to copy at the pinned revision.

## ktdi observations

Source revision: `dbefaf671b0937db6d9e9ad3dd862f3f1c707103`.
File read on 18 October 2026: `ARCHITECTURE.md`.

Observed:

- It describes a root launcher, package configuration, one SQLite file,
  rotating logs, separate live and development bot settings, and SQLite backup
  through the backup API.
- Server-owned rows normally record `guild_id`, and server-scoped reads use a
  database-owned scope condition.
- Daily schedules use a configured timezone, store UTC instants, apply a grace
  period, and advance after failures.
- Its documented Discord embed limits are 1,024 characters per field, 6,000
  characters in total, and 25 fields.
- Its fakes use a function named `run`; the project specification explicitly
  says not to carry that name into this repository because datum rule 0.5
  prohibits it.

Conclusion: the selected patterns in sections 3.2 and 5.3 of the project
specification are supported by the inspected architecture document. Discord
limits still require verification from Discord's official documentation.

## Findings requiring resolution

### EF1: datum reference path mismatch

The datum names `https://github.com/FtrOnOff/FtrIO`, but the local FtrIO
repository records `https://github.com/TheScottBot/FtrIO.git`. The datum forbids
substituting a similar repository. The exact named upstream must be verified
before its contents can satisfy the Plan-stage reference requirement.

### EF2: KD7 has no referenced licence

ProcBot has no `LICENSE` file at its pinned revision. Selecting the licence
ProcBot uses is therefore not a concrete option on the evidence inspected. The
author must choose a licence explicitly before KE1.

Update, 18 October 2026: the author stated that licences had been added and
that they are MIT. The local pinned ProcBot and target checkouts did not yet
contain those new files when checked, which is consistent with the reference
checkout predating the author's change. The author explicitly selected MIT for
this project, so KD7 is resolved. The project `LICENCE` file remains future KE1
work and must carry the author-selected holder and year.

### EF3: live Discord remains an author gate

No live token or Discord server will be used by the agent. Discord behaviour
that official source and isolated experiments cannot settle remains for the
author's KE8 checks.

### EF4: no project Python environment exists yet

The Windows Python launcher reported that no installed Python was available,
and the `python` command resolved to an inaccessible Microsoft Store alias. The
existing ProcBot virtual environment reported Python 3.14.7. This proves that a
usable interpreter exists locally, but does not settle the Python version on
the author's homelab. No environment was created for this repository during the
Plan stage.

## Official Discord documentation

Sources read on 18 October 2026:

- `https://docs.discord.com/developers/interactions/application-commands`
- `https://docs.discord.com/developers/events/gateway`
- `https://docs.discord.com/developers/resources/message`
- `https://docs.discord.com/developers/topics/permissions`

Observed:

- Discord defines message commands as application commands invoked from a
  message's context menu. The interaction includes the selected message in its
  resolved payload.
- Discord's gateway documentation explicitly exempts the message selected by a
  message context menu command from the message-content intent restriction.
- `MESSAGE_CONTENT` remains a privileged intent for general message content.
  The bot does not need it for the command and menu design in the specification.
- A message is limited to 2,000 content characters.
- An embed permits up to 25 fields, 1,024 characters in each field value, and
  6,000 characters across the counted fields of all embeds in one message.
- Sending a message in a guild channel requires `SEND_MESSAGES`. Discord lists
  `EMBED_LINKS` separately and says that denying `SEND_MESSAGES` also denies
  `EMBED_LINKS` implicitly.
- Sending in a thread uses the separate `SEND_MESSAGES_IN_THREADS` permission.
- `MANAGE_GUILD` is permission bit 5. Discord supports making it a command's
  default member permission.
- The `applications.commands` OAuth scope is automatically included with the
  bot scope.

Conclusions:

- KU6 is settled at 2,000 characters for message content.
- KU7's message-menu assumption is supported by Discord's official
  documentation. Default gateway intents are sufficient for the specified
  interaction design.
- KU10 is settled for field value, field count, and aggregate embed limits.
- The proposed `SEND_MESSAGES` and `EMBED_LINKS` bot permission set supports
  posting in ordinary guild text channels. The specification must either
  exclude thread channels from daily setup or add `SEND_MESSAGES_IN_THREADS`.
  This is a Plan-stage contract question because the current text says only
  `this channel`.

Update, 18 October 2026: the author approved the additional thread permission
and left thread support to the implementation. Krill Bot will support daily
posting in threads and request `SEND_MESSAGES`, `EMBED_LINKS`, and
`SEND_MESSAGES_IN_THREADS`. KU7 is settled for KE1. The required invite
permission integer is 274877925376.

## Exact FtrIO upstream

Source read on 18 October 2026:
`https://github.com/FtrOnOff/FtrIO`.

Observed: the exact repository named by the datum exists publicly. Its default
branch is `main`, GitHub showed 34 commits when read, and the repository declares
an MIT licence. The source tree shown by GitHub includes `.github/workflows`,
`FtrIO`, `assets`, `docs`, `CHANGELOG.md`, `LICENSE`, and `README.md`.

Conclusion: EF1's mismatch is confined to the local checkout's recorded origin.
The exact upstream exists and must be the source used for the datum's reference
review. Its precise revision still needs to be recorded before the review is
complete.

## Python reference style

Source revision: `b95ec4e1feaf1b3c74a30a43edd5e03c90f7ad68` from
`https://github.com/FtrOnOff/ftrio-python.git`.

Files read on 18 October 2026: `pyproject.toml`, `.github/workflows/ci.yml`,
`tests/conftest.py`, `tests/unit/test_lint.py`, and `ftrio/config.py`.

Observed:

- The package uses the standard `src`-free package layout, pytest's
  `test_*.py` naming, shared fixtures in `tests/conftest.py`, and descriptive
  fake types.
- Its CI tests a Python-version matrix and runs Ruff, MyPy, and Pytest.
- Its Ruff configuration favours descriptive names and enforces imports,
  upgrades, likely bugs, and Python naming conventions.
- Its MyPy configuration is not strict. This bot must use the stricter setting
  required by its own specification.
- Tests isolate ambient global state with an automatic fixture and restore it
  after every test.
- Comments generally describe rationale or cross-runtime behaviour, although
  some source comments and test headings use typography prohibited by datum
  rule 0.8. Those characters must not be copied.

Conclusion: adopt its descriptive Python structure, fixture isolation, native
test naming, and CI separation. Do not copy its weaker type-checking settings or
prohibited typography.

## Rust reference style

Source revision: `e814d40758eb3524d64e9e40688bb8c59de65989` from
`https://github.com/FtrOnOff/ftrio-rust.git`.

Files read on 18 October 2026: `docs/EVALUATION.md` and
`.github/workflows/ci.yml`.

Observed:

- The evaluation record precedes implementation and distinguishes faithful
  behaviour from language-specific surface choices.
- Unavoidable differences are named explicitly and linked to a deviation log.
- CI checks formatting, lint warnings as errors, all tests, a supported minimum
  toolchain, and a standalone example that could otherwise decay unnoticed.

Conclusion: use the same evidence-first structure and make supported-version
claims executable in CI. Rust syntax and naming conventions do not transfer to
the Python implementation.

## Locally proven dependency versions

The ProcBot environment was inspected on 18 October 2026. Installed package
metadata recorded:

| Package | Version | Python requirement | Declared licence |
|---|---|---|---|
| `discord.py` | 2.7.1 | 3.8 or later | MIT |
| `python-dotenv` | 1.2.4 | 3.10 or later | BSD-3-Clause |
| `tzdata` | 2026.5 | Python 2 or later | Apache-2.0 |
| `pytest` | 9.1.1 | 3.10 or later | Metadata inspected did not expose a single `License` field. |

Hypothesis, Ruff, and MyPy were not installed in that environment. This table
proves local availability only. It is not yet the full datum rule 0.13 record,
and it does not select project version bounds.

### Current development-tool releases

PyPI project metadata was read on 18 October 2026:

| Package | Current release | Python requirement | Licence | Published capability relevant here |
|---|---|---|---|---|
| `pytest` | 9.1.1 | 3.10 or later | MIT | Native assertion reporting, discovery, and fixtures. |
| `hypothesis` | 6.167.1 | 3.11 or later | MPL-2.0 | Property-based generation and shrinking for parser fuzz properties. |
| `ruff` | 0.16.8 | 3.7 or later | MIT | Python 3.14 compatible linting and formatting with built-in rule sets. |
| `mypy` | 2.4.0 | 3.10 or later | MIT | Strict static analysis and declared Python 3.14 support. |

All four projects identify active 2026 releases and maintained upstream source
repositories. They are development-only dependencies and do not ship with the
bot. Ruff is a platform-specific binary distribution; the other three publish
portable Python wheels. Replacement would mean selecting another test runner,
property-based test library, linter, or type checker and rewriting the
corresponding checks. Tests will exercise pytest and Hypothesis directly; CI
will invoke Ruff and MyPy against the whole owned tree.

Conclusion: KU8 can use these current releases if the homelab runs Python 3.11
or later. Current Hypothesis no longer supports Python 3.10, so KU11 must be
settled before the project's Python floor and dependency bounds can be chosen.

Update, 18 October 2026: the author chose the Python version proven on the
development device and confirmed that both the homelab and deployment droplet
can run it. The project therefore targets Python 3.14, with Python 3.14.7 as the
development version observed during planning. KU11 is settled. The current
development-tool releases above all support Python 3.14, so KU8 is settled to
those versions for KE1.

Installation on 18 October 2026 selected Hypothesis 6.170.1 and Ruff 0.17.1
under the declared compatible lower bounds. Pytest 9.1.1 and MyPy 2.4.0 matched
the versions recorded above. The evaluation record retains the earlier PyPI
observation as history rather than rewriting it.

## Published Krillion pages

Sources read on 18 October 2026:

- `https://krillion.io/`
- `https://krillion.io/faq`
- `https://krillion.io/privacy`
- `https://krillion.io/archive`
- `https://krillion.io/packs`
- `https://krillion.io/unlimited`

Only rendered page content returned by the fetch service was read. Site scripts
were not read, in accordance with the project specification.

Observed:

- The home page states that the daily dive has seven prompts, 25 seconds per
  prompt, the same prompts for everyone, and one dive per day.
- The home page says that every point represents ten metres and that 700 is the
  trench reached by a perfect dive. This is evidence for a maximum perfect
  score, but it does not by itself define the parser's complete score grammar.
- The navigation distinguishes Daily dive, Unlimited, Archive, and Themed
  packs. The rendered pages do not show the Copy result format for any mode.
- The privacy page, effective 23 September 2026, confirms that Copy result
  contains the daily number, score, and emoji row without a name or answers.
- The privacy page confirms that Discord Activity recap posts occur after the
  daily reset, but does not state the reset time or timezone.
- The FAQ identifies the maker as `kp`, says Krillion is made by one person,
  warns about copycat attribution, and gives `business@krillion.io` for
  partnerships and collaborations.
- Direct fetches of likely terms paths did not return a readable terms page.
  This is not proof that no terms exist.

Conclusions:

- KU1 remains open because the published rendered pages do not define the Copy
  result grammar or distinguish each mode's copied result.
- KU2 gains evidence that 700 is the perfect-dive score. A hard parser bound
  remains provisional until samples or a direct statement settle it.
- KU4 remains open because the reset instant and daily-number mapping are not
  published in the pages inspected.
- KD1 remains an author decision. The published material strengthens the case
  for using a distinct identity and contacting the maker before a public
  listing.

## Author-observed scoring update

Source: the author's direct observation from playing Krillion on 18 October
2026. This is an author observation, not a claim read from Krillion source.

Observed round results:

| Round description | Other players choosing it | Points | Emoji |
|---|---:|---:|---|
| no answer | not applicable | 0 | ⬛ |
| very common answer | 79,986 | 10 | 🫧 |
| uncommon answer | 364 | 60 | 🦑 |
| rare answer | 195 | 85 | 🏮 |
| very rare answer | 16 | 85 | 🏮 |

Conclusions:

- The current observation supports the existing values for ⬛, 🫧, 🦑, and 🏮.
- Two distinct rarity descriptions can map to the same 🏮 symbol and 85 points.
- 🐟 did not appear in the supplied round table. The observation does not
  establish whether its 30-point value remains current or whether that tier was
  removed or renamed.
- No Krillion-gem or higher-valued symbol appeared, so KU12 remains open.
- The published claim that 700 is a perfect dive cannot be reconciled with a
  maximum observed round value of 85 without another tier, another scoring
  rule, or a changed published scale. No parser check may assume an answer.
- The Copy result block from this play was not supplied, so this observation is
  evidence for scoring but is not a KD6 parser fixture.

## Open decisions

KD7 is resolved as MIT by the author's decision on 18 October 2026. KD1 through
KD6, KD8, and KD9 remain open until the author answers them explicitly.

KD2 was resolved by the author on 18 October 2026: the bot's display name is
`Krill Bot`. The derived Python package and systemd service identifier is
`krillbot`. Public-facing descriptions must state plainly that Krill Bot is an
unofficial companion for Krillion so that the name cannot imply ownership or
endorsement.

KD2 and KD7 no longer block KE1. KU8 and KU11 still require evidence before KE1
is settled. The remaining decisions block the later phases identified in the
project specification.

Update, 18 October 2026: the author settled the daily reset for KE5. Each
server sets its reset time with its `/setup daily` command. A server that sets
none uses a reset time from the bot's environment file, and when that is
absent too, 04:00 each day. The author also accepted the current streak rule,
under which a current streak counts only once the player has logged the
server's newest daily number.

Update, 18 October 2026: the author answered the remaining KE5 and KD3
questions. KD3 is settled as private: Krill Bot runs only on servers the author
adds it to and is not listed publicly. Retention was not stated separately, so
no pruning is built; rows stay until `/dive forget` or removal deletes them,
which is the behaviour already specified, and pruning would be a later
decision. KU5 is settled: the daily post time is its own setting, chosen per
server in `/setup daily`, falling back to a value in the bot's environment
file and then to 17:00. The reset and post times, and both fallbacks, are read
in `BOT_TIMEZONE`.

## Experiments performed

1. Inspected the target repository with read-only filesystem and Git commands.
   Result: it was empty and had no commits.
2. Inspected the recorded origins and revisions of the six local reference
   repositories. Result: the three project references matched their specified
   revisions; the datum's FtrIO path did not match the local origin.
3. Attempted to read ProcBot's `LICENSE` at its pinned local revision. Result:
   the file did not exist.
4. Opened the exact FtrIO path named by the datum on GitHub. Result: the public
   repository exists; the similarly named local checkout has a different
   recorded origin.
5. Read Discord's official application-command, gateway, message, and permission
   documentation. Result: KU6 and KU10 are settled, and KU7's context-menu
   content assumption is supported. Thread posting needs a separate permission.
6. Queried the available Python commands. Result: no project interpreter exists;
   ProcBot's existing environment runs Python 3.14.7.
7. Inspected the Python and Rust datum references for layout, naming, test
   isolation, CI, evaluation, and deviation practices. Result: transferable
   approaches were identified without copying language-specific conventions.
8. Inspected installed package metadata in ProcBot's environment. Result: four
   locally proven versions were recorded; three development tools remain absent.
9. Read the published Krillion home, FAQ, privacy, Archive, pack, and Unlimited
   pages through a rendered-page fetch service. Result: the basic daily-game and
   privacy claims were confirmed, while the result grammar and reset time remain
   unpublished in the material inspected.
10. Checked the target, pinned ProcBot, and current remote reference locations
    after the author's licence update. Result: the local files had not changed
    and the web fetch did not expose the new files. The author's direct MIT
    decision nevertheless settles KD7 for this project.
11. Recorded the author's name decision. Result: KD2 is settled as `Krill Bot`,
    with `krillbot` as the derived code and service identifier and an explicit
    unofficial status in public copy.
12. Read current PyPI metadata for the four development dependencies. Result:
    current pytest, Ruff, and MyPy support Python 3.10 or earlier floors, while
    current Hypothesis requires Python 3.11 or later. KU8 therefore depends on
    the homelab version in KU11.
13. Recorded the author's runtime and thread-permission decisions. Result: the
    project targets Python 3.14, uses the current KE1 development tools, and
    supports daily posting in threads with the additional Discord permission.
14. Recorded the author's observed updated scoring table. Result: four symbol
    values remain supported, two rarity descriptions share 🏮 and 85 points,
    while 🐟, any higher tier, and the 700-point published scale remain
    unresolved.
15. Planted a repository check requiring every declared dependency and every
    datum 0.13 field. Result: the focused suite failed because `DEPENDENCIES.md`
    was absent, then passed after the complete record was added.
16. Recorded the author's licence-holder decision as `TheScottBot`, then planted
    a repository check for the selected MIT licence. Result: the focused suite
    failed because `LICENCE` was absent before the standard licence text was
    added, then the complete suite passed.
17. Recorded the author's approval to begin KE2 within the known evidence
    boundary. Parser tests first failed at collection because the grammar API
    did not exist, then 26 focused tests passed after the pure implementation.
18. Planted a repository check for a distinct parser fuzz gate. Result: the
    check failed because continuous integration ran only the general suite,
    before the explicit parser-property step was added.
19. The author changed the parser policy to tolerate new round emoji and any
    non-negative copied score. Revised tests failed against the closed symbol
    model, then passed after unknown rows became opaque and the parser exposed a
    recognised-symbol subtotal plus a conservative validation signal.
20. Planted KE3 tests for exact storage, replacement, server isolation, private
    replies, refusal privacy, and message authorship. Result: nine focused tests
    failed because the query and command interfaces did not exist, then the
    focused slice passed after their implementation.
21. The author selected no KU9 aggregate refusal threshold or format-change
    warning. A revised command test failed against the former generic rejection
    copy before the author-supplied private guidance was centralised. The
    authorised specification departure is recorded in
    `IMPLEMENTATION_DEVIATIONS.md`.
22. The author selected hidden scores by default, total-score board ranking with
    dives, average, and best, and rolling 7-day and 30-day periods based on daily
    numbers. Pure KE4 tests failed at collection because the board model did not
    exist, then eight focused tests passed after implementation.
23. Planted the second KE4 slice for server-scoped reads, hidden-today access,
    rolling board commands, private paging, and streak replies. Result: six
    focused tests failed at missing interfaces before implementation, then all
    17 focused database and command tests passed.
24. Read Discord's message documentation again for the embed description limit,
    which the earlier record omitted. Result: a description holds 4,096
    characters and a title 256, alongside the recorded 2,000-character content
    and 6,000-character aggregate limits.
25. Planted the third KE4 slice for daily bearings, embeds-owned board titles,
    description and content limits with a truncation note, exact averages, and
    a wider displayed-string check. Result: eleven focused tests failed for the
    expected reasons, including an `OverflowError` from a float average of a
    score beyond float range, then all 81 tests passed. The wider check, run
    against the committed `commands.py`, reported the two composed board titles
    and the inline `/help` description.
26. Read ProcBot's `/setup` group at `2c7ac2d` and discord.py 2.7.1's
    `Group` signature and `has_permissions` check. Result: ProcBot sets
    `guild_only` and a Manage Server `default_permissions`, and its own notes
    say a server can change who sees the command. The check reads
    `interaction.permissions` and raises `MissingPermissions`, a
    `CheckFailure`, which the existing error handler already answers privately.
27. Planted the first KE6 slice for `/setup visibility`, `/setup show`, the
    Manage Server requirement, per-server idempotent visibility storage, and
    the daily post read. Result: seven focused tests failed at missing
    interfaces, then all 88 tests passed.
28. Read the Python 3.14 development mode documentation for datum 0.10's memory
    and undefined behaviour analysis, which KE1 had not recorded in
    `TESTING.md` as specification section 5.4 requires. Result: `-X dev`
    installs the allocator debug hooks, faulthandler, resource and deprecation
    warnings, and eager encoding checks; the page does not present it as a
    sanitiser. Two repository tests for the record and the gate failed before
    either existed. A planted test leaking an unclosed SQLite connection passed
    under plain Pytest and failed under `python -X dev -m pytest -W error`,
    after which the gate was added to continuous integration and all 90 tests
    passed under both commands.
29. Read ProcBot's `daily.py`, its daily database functions, its `/setup daily`
    commands and its loop at `2c7ac2d`, and discord.py 2.7.1's `tasks.loop`,
    `Loop.__get__`, `Client.get_channel` and `HTTPException`. Result: ProcBot
    uses a one-minute loop, a six-hour grace period, one post per server, and
    always moves on to the next day in a `finally` block. `get_channel` returns
    threads as well as channels.
30. Planted the time grammar and environment fallbacks. Result: the new
    `clock.py` tests failed at collection, the three configuration tests and
    the pure-import case failed, then all passed. A test that `.env.example`
    names both fallbacks failed against a planted copy without them.
31. Planted schema version 2 and the daily post storage. Result: five focused
    tests failed at missing interfaces, then all 124 tests passed. A version 1
    database upgrades with its rows kept.
32. Planted `daily.py`: due times, both fallbacks, yesterday's board from the
    window between the previous two resets, server isolation, the no-results
    message, the grace-period skip, a failed send, a missing channel, and one
    server's failure leaving another's post intact. Result: the module failed
    at collection, then all 135 tests passed.
33. Planted `/setup daily here`, `stop` and `show`, and the daily post shown by
    `/setup show`. Result: eight focused tests failed at missing interfaces,
    then all 143 tests passed.
34. Planted the one-minute loop, its start on ready, and its delegation to the
    daily post. Result: three focused tests failed, then all 146 tests passed,
    including under `python -X dev -m pytest -W error`.
35. Read discord.py 2.7.1's `View` and `BaseView` constructors, `Button`, and
    `RawThreadDeleteEvent`, and ProcBot's removal handlers at `2c7ac2d`.
    Result: a view can be built without a running event loop, in which case
    its stop future is absent; the raw thread event carries the thread and
    server identifiers even for uncached threads.
36. Planted origin-recorded deletions: counting, forgetting here and
    everywhere, forgetting a server, stopping a deleted channel's post, and an
    origin for `/setup daily stop`. Partial failure was planted as an SQLite
    trigger that aborts the server removal midway. Result: seven focused tests
    failed, then all 153 tests passed; the interrupted removal left every row,
    and the retry removed exactly the server's rows.
37. Planted removal from a server, channel deletion and thread deletion in the
    client. Result: three focused tests failed, then all 156 tests passed.
38. Planted `/dive forget` with its caller-only confirmation. Result: nine
    focused tests failed at the missing command. Two assertions on the view's
    `is_finished` could not hold without an event loop, because that state is
    the future the constructor skips; they were removed before ever passing,
    leaving the observable removal of the buttons asserted. All 165 tests then
    passed under plain Pytest and development mode.
39. Computed the requested permission integer with discord.py 2.7.1 and read
    ProcBot's `docs/DISCORD_LISTING.md` at `2c7ac2d`. Result: Send Messages,
    Embed Links and Send Messages in Threads give 274877925376, matching the
    earlier record.
40. Planted the KE7 document tests: every stored table and column named in
    `PRIVACY.md`, its section 6.1 contents, the two trust boundaries and
    accepted risks in `SECURITY.md`, and the permission integer in the
    listing. Result: four tests failed for missing files, then passed once the
    documents were written. A copy of `PRIVACY.md` without `reset_clock`
    failed the column test naming `daily_posts.reset_clock`, and a listing
    with the wrong integer failed its test.
41. The author decided the private bot needs no application ID and no invite
    link. The draft invite section was removed and its new, never-committed
    test now checks the permission integer instead of the invite query.
42. Read ProcBot's `docs/` site at `2c7ac2d`: `.nojekyll`, `index.html`,
    `style.css`, and hand-written `privacy.html` and `terms.html`. The author
    asked for the site with terms and privacy pages although Krill Bot is
    private.
43. Planted `site_builder.py`, which generates `docs/privacy.html` and
    `docs/terms.html` from `PRIVACY.md` and `TERMS.md`, refuses Markdown it
    does not understand, and has a `--check` mode for continuous integration.
    Result: the module failed at collection, then the converter's tests
    passed while four tests failed for the missing pages, terms, CI step and
    `.nojekyll`; all passed once those were added. Appending a planted
    sentence to `PRIVACY.md` made `--check` fail naming `docs/privacy.html`.
    The privacy page rendered at 375 pixels wide with no sideways scrolling.
    The typography scan and Ruff each caught one defect in the first draft,
    both fixed before the suite passed with 182 tests under plain Pytest and
    development mode.

## KE2 progress report, 18 October 2026

Implemented so far: six author-supplied daily fixtures, the strict known
four-line grammar, surrounding-conversation matching, Discord's 2,000-character
input bound, single-result enforcement, the five-symbol inferred score table,
score-mismatch metadata, and the published bearing bands.

The focused suite covers every real fixture, malformed and unknown rows,
multiple results, surrounding conversation, all bearing edges, accepted score
mismatches, and three bounded Hypothesis properties. The pure-module import
check remains in force, and continuous integration has a distinct parser fuzz
step.

The approved boundary deliberately does not guess result markers for Unlimited,
Archive, or packs, any new round symbol, the reset time, or the daily-number to
date mapping. Therefore `not-daily` and `from-the-future` cannot yet be emitted.
These are recorded limitations, not silently invented behaviour.

KE2 is implemented to the author-approved evidence boundary but is not complete
against the full draft specification until genuine fixtures settle those two
rejection cases and any additional round symbol.

Update, 18 October 2026: the author superseded the closed-symbol boundary.
Unknown round emoji must now be accepted so game changes do not stop logging.
Known points are totalled, but a score is considered checked only when the whole
row is recognised. A fully known row retains the seven-symbol check. A row with
an unknown symbol remains opaque because the standard library cannot reliably
segment every composed emoji. Additional symbols no longer block KE2; genuine
non-daily fixtures and reset mapping still do.

## KE3 progress report, 18 October 2026

Implemented so far: atomic server-scoped result insertion and replacement,
newest-first personal history, `/dive log`, private `/dive me`, and the Log
Krillion result message menu. The menu refuses messages not written by the
caller. Refused text is neither stored nor logged; the log records only the
server and stable rejection reason. Accepted rows store only the six schema
columns, and an unverified score records only a server-scoped diagnostic.

KE3 is complete to the author's revised contract. Daily aggregate refusal
counters and the format-change warning are intentionally omitted. Each
unrecognised paste receives private guidance, while only its server and stable
reason enter the diagnostic log.

## KE4 progress report, 18 October 2026

Implemented so far: pure board entries and standings, rolling week and month
cutoffs, all-time aggregation, total-score ranking, dives, average, best, and
current and longest streak calculations. Board ties are resolved by best score,
then dives, then Discord user ID so results remain deterministic. Duplicate
daily numbers do not inflate streaks, and a gap breaks them.

Implemented command surface: `/dive today`, `/dive board`, and `/dive streak`.
Today is hidden by default until the viewer logs the latest server result.
Database reads always include `guild_id`. Long boards use private twenty-row
pages, and every page disables mentions. Until KU4 is settled, views use the
highest daily number logged in the server as their rolling anchor, which is
recorded rather than presented as Krillion's actual reset date.

KE4 is complete to the available reset evidence. The `/setup visibility`
control that changes the default belongs to KE6.

Update, 18 October 2026: a review of the second slice against the
specification found four gaps, closed by a third slice. `/dive today` did not
show each score's bearing, as section 2.1 requires; it now does, derived from
the bearing table. Board titles were composed in `commands.py`, outside
`embeds.py`, which the displayed-string check missed because it inspected only
literals passed directly to a send method. Nothing enforced Discord's limits
from section 5.3: a board row carrying an unbounded score could exceed the
4,096-character description limit, and `/dive me` would exceed the
2,000-character content limit after roughly fifty dives. Pages now break by
twenty rows or by the description limit, whichever comes first; a single row
too long for a page and an over-long history are truncated with a note, with
the oldest results dropped first. Lengths are measured in UTF-16 code units,
never fewer than Discord's count, because Discord does not say how it counts an
emoji. Board averages are now exact fractions, because a score beyond float
range raised `OverflowError` and broke every board in the server.

The wider displayed-string check also caught the inline `/help` command
description written in KE1. It was moved into `embeds.py` in the same slice,
because the check could not pass on the tree otherwise. The all-time board
title reads `All-time board` rather than the former `All board`.

## KE8 author gates, 18 October 2026

The author ran the development bot in a test server and reported the five
checks the agent listed as passing, in the words recorded in `TESTING.md`.
The agent did not observe them. The repository was at `0de6887` with no code
changes outstanding when the report was given. KE8's done-when criterion, the
author recording each check in `TESTING.md`, is met by that recorded
statement; it does not cover live behaviour beyond the five checks named.

## KE7 progress report, 18 October 2026

Implemented so far: `PRIVACY.md`, `SECURITY.md` and `docs/DISCORD_LISTING.md`,
with tests that keep the privacy record naming every stored column and the
listing naming the exact permission integer, and a README describing the
current commands. The prose scan already covers `docs/`.

The privacy wording and the accepted risks were drafted by the coding agent
from the code and specification. Datum Part 2 asks for the accepted risks in
the author's own words, so both are the author's to rewrite before KE7 is
complete. KD3 makes Krill Bot private, so no invite link, App Directory copy
or application ID is recorded. Whether the GitHub Pages site with terms and
privacy pages, and the icon, banner and presence assets, are still wanted for
a private bot is open.

Update, 18 October 2026: the author asked for the site. `docs/` now holds
`.nojekyll`, a hand-written `index.html`, `style.css`, and `privacy.html` and
`terms.html` generated from `PRIVACY.md` and `TERMS.md`, with a CI check that
they match. `TERMS.md` is also agent-drafted and the author's to reword.
Serving the site needs GitHub Pages enabled for `docs/` on the main branch,
which is the author's repository setting. No icon, banner or presence image
exists yet: artwork is the author's to supply, and the pages use no images in
the meantime.

## KE5 progress report, 18 October 2026

Implemented so far: the pure `clock.py` time grammar shared by the
environment file and `/setup daily`; the `DAILY_POST_TIME` and
`DAILY_RESET_TIME` fallbacks, defaulting to 17:00 and 04:00 in
`BOT_TIMEZONE`; schema version 2, which lets a server leave either time unset
and stores its reset time; `daily.py`; `/setup daily here [time] [reset]`,
`stop` and `show`; and the one-minute loop.

The post says today's dive is open, links to krillion.io, and carries
yesterday's board. Yesterday's dive is the newest daily number logged in this
server between the previous two resets, so it follows each server's own reset
without the daily-number to date mapping that KU4 still lacks. A post is
skipped and logged after a six-hour grace period, a failed send or missing
channel is logged with the server, and every due post moves on to its next
day. Every message is sent with mentions disabled. An unexpected error for one
server is logged and the loop carries on, because an exception escaping a
`tasks.loop` iteration would stop it for every server.

The loop starts on ready rather than in `setup_hook` as ProcBot does. Starting
a `tasks.loop` needs a running event loop, and the KE1 `setup_hook` test
completes that hook without one; on ready also keeps the loop to a client that
is connected. Ready fires again after a reconnect, so the start is guarded.

Not yet attached under `/setup`. Nesting the `daily` group there changes the
exact subcommand list asserted by the KE6 test
`test_setup_is_server_only_and_defaults_to_manage_server`. Datum 0.4 forbids
editing that assertion without raising it, so the change waits for the author.

Update, 18 October 2026: the author approved extending that assertion with the
daily subcommands. It failed while `daily` stood apart, then all 146 tests
passed, under plain Pytest and development mode, once the group was attached
with `/setup` as its parent. The commands are `/setup daily here`,
`/setup daily stop` and `/setup daily show`; the subgroup inherits `/setup`'s
server-only and Manage Server defaults, and each subcommand keeps its own
Manage Server check.

The daily post's real sending, timing and thread behaviour are author gates
under KE8. The `from-the-future` refusal still needs KU4's date mapping.

## KE6 progress report, 18 October 2026

Implemented so far: `/setup visibility`, which stores whether `/dive today`
hides scores until the viewer has logged, per server and idempotently, and
`/setup show`, which privately reports that choice and the daily post. The
group is server-only with Manage Server as its default permission, and every
subcommand also checks Manage Server when used, because a server can widen who
sees a command beyond its default.

Not yet registered with the client. Adding the group to `APPLICATION_COMMANDS`
changes the exact command list asserted by the KE1 test
`test_client_uses_default_intents_without_privileged_message_content`. Datum
0.4 forbids editing that assertion without raising it, so the change waits for
the author.

Update, 18 October 2026: the author approved adding `setup` to that assertion.
The extended assertion failed because the group was unregistered, then all 88
tests passed after `setup_group` was added to `APPLICATION_COMMANDS`.

`/dive forget` and deletion on server removal and channel deletion wait for
KD3. The daily post shown by `/setup show` is always `Not set up` until KE5
writes one.

Update, 18 October 2026: with KD3 settled as private and KE5 built, the rest of
KE6 is implemented. `/dive forget scope:here` or `scope:everywhere` says how
many results it will delete and waits for a Delete or Cancel button that only
the caller passes the check for; anyone else is answered privately and
nothing changes. Removal from a server deletes its results, daily post and
settings in one transaction; deleting a channel or thread stops a daily post
held there. Every deletion takes a required origin, `forget-command`,
`guild-removed`, `channel-deleted` or `setup-daily-stop`, and logs it with the
server and a count, never a user. Each is idempotent. The server removal was
tested for an interruption midway: it left every row, and a retry finished it.

The live confirmation flow, removal and deletion events remain author gates
under KE8. A confirmation unanswered for two minutes stops accepting presses;
its buttons stay visible, since the private reply is not edited on timeout.

## KE1 progress report, 18 October 2026

Implemented so far: package and stable launchers, validated environment
configuration, schema version 1, refusal of newer schemas, the `/help` command,
default Discord intents, development-guild command sync, private command-error
responses, privacy-safe command logging, rotating file logging, executable tree
checks, project metadata, continuous integration, and the hardened systemd
service.

Test-first evidence:

- The initial focused suite failed during collection because `krillbot` did not
  exist, then passed five tests after the minimum package and schema work.
- The portable-import check was run against a deliberately planted `sqlite3`
  import. It failed one test, then passed after the violation was removed.
- The command, bot, and tree-check slice failed because its modules did not
  exist, then passed after the minimum implementation.
- Repository-contract tests failed for missing packaging, environment, CI, and
  service files before those files were added.
- Command logging and lifecycle tests failed for missing callbacks before those
  callbacks were implemented.

Current automated results on Windows with Python 3.14.7:

- repository policy checks: passed
- Ruff lint: passed with no findings
- Ruff format check: 28 files formatted
- MyPy strict analysis: 10 source files passed with no issues
- Pytest: 71 passed in 3.42 seconds
- warnings: none reported
- skipped tests: none

The managed environment could not use its default temporary directory, so
dependency installation used `.sandbox-temp` and Pytest used an ignored base
directory below `.pytest_cache`. Its event loop also hung on a minimal
`asyncio.sleep(0)` experiment, so fake-only command coroutines were completed
directly. This does not clear any live Discord author gate.

KE1 automated implementation is complete. The MIT licence is attributed to the
author-selected holder `TheScottBot`, and the datum 0.13 dependency record is in
`DEPENDENCIES.md`. The remaining always-required documents belong to their later
specification phases. KE1's clean-machine reproduction remains an author gate
and has not been claimed by the coding agent.

No implementation, behavioural test, external mutation, live Discord action, or
Git write operation was performed.
