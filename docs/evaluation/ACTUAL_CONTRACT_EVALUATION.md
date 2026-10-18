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
- Pytest: 49 passed in 2.25 seconds
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
