# Dependency record

Recorded on 18 October 2026 before the dependencies were adopted. Versions are
the compatible lower bounds declared in `pyproject.toml`. No dependency is
vendored into this repository.

## discord.py

- Behaviour provided: Discord gateway, interaction, application command, embed,
  permission, and HTTP client support.
- Why the standard library or platform is insufficient: Python does not provide
  Discord's authenticated gateway and interaction protocol.
- Maintenance status: active release 2.7.1 was installed and inspected locally.
- Licence: MIT.
- Size: the largest runtime dependency, including protocol models and HTTP and
  gateway support; installed as a Python package rather than vendored.
- Platform support: Python 3.8 or later on supported Python platforms; the
  project uses it on Python 3.14.
- Security implications: receives untrusted Discord payloads and holds the bot
  token in process memory; upgrades require review for authentication, gateway,
  and request changes.
- Test strategy: fake Discord objects cover owned command behaviour; real
  registration and gateway behaviour remain an author gate with a development
  bot.
- Replacement cost: high because commands, interactions, embeds, and lifecycle
  integration use its public interfaces.

## python-dotenv

- Behaviour provided: loads local `.env` and `.env.dev` settings into the
  process environment.
- Why the standard library or platform is insufficient: Python has no standard
  dotenv file parser.
- Maintenance status: active release 1.2.4 was installed and inspected locally.
- Licence: BSD-3-Clause.
- Size: one small pure Python configuration package.
- Platform support: Python 3.10 or later on supported Python platforms.
- Security implications: reads files that may contain the Discord token;
  configuration fixes must never print or persist secret values.
- Test strategy: configuration tests disable dotenv loading and isolate the
  process environment.
- Replacement cost: low; a small owned parser or deployment-only environment
  configuration could replace it.

## tzdata

- Behaviour provided: supplies current IANA timezone records when the operating
  system does not provide them to `zoneinfo`.
- Why the standard library or platform is insufficient: `zoneinfo` contains the
  reader but Windows does not normally ship the IANA database it reads.
- Maintenance status: active 2026.5 release was installed and inspected locally.
- Licence: Apache-2.0.
- Size: a compact data-only wheel containing the IANA timezone database.
- Platform support: portable Python data used on platforms without system zone
  information and harmless where system records are available.
- Security implications: stale timezone rules could schedule a post at the
  wrong civil time; the package processes no user input and holds no secret.
- Test strategy: daily scheduling tests will cover timezone conversion and
  daylight-saving boundaries before KE5.
- Replacement cost: low on Linux with system timezone records, but retaining it
  keeps development and deployment behaviour consistent.

## pytest

- Behaviour provided: test discovery, fixtures, parametrisation, assertions,
  and failure reporting.
- Why the standard library or platform is insufficient: `unittest` could run
  tests but does not provide the selected concise fixture and parametrisation
  model.
- Maintenance status: active release 9.1.1 was current when selected.
- Licence: MIT.
- Size: development-only Python tooling and its declared transitive packages;
  absent from the deployed runtime dependency set.
- Platform support: Python 3.10 or later on supported Python platforms.
- Security implications: test plugins execute Python during development and CI;
  only declared dependencies are installed and no untrusted plugins are loaded.
- Test strategy: continuous integration invokes Pytest for every pull request.
- Replacement cost: medium because all tests and fixtures use its discovery and
  assertion conventions.

## Hypothesis

- Behaviour provided: generated examples and shrinking for parser properties.
- Why the standard library or platform is insufficient: Python has no standard
  property-based test generator or failure shrinker.
- Maintenance status: active release 6.167.1 was current when selected; local
  installation resolved to 6.170.1.
- Licence: MPL-2.0.
- Size: development-only Python tooling; absent from the deployed runtime
  dependency set.
- Platform support: Python 3.11 or later on supported Python platforms.
- Security implications: generated input can consume test resources; CI uses a
  bounded profile and the library is never imported by the bot runtime.
- Test strategy: KE2 parser properties will run in the ordinary Pytest suite and
  in the explicit continuous integration fuzz step.
- Replacement cost: medium because replacing generation and shrinking would
  require rewriting the parser property suite.

## Ruff

- Behaviour provided: Python linting, import checks, likely bug checks, naming
  checks, and deterministic formatting.
- Why the standard library or platform is insufficient: Python ships no
  equivalent linter or source formatter.
- Maintenance status: active release 0.16.8 was current when selected; local
  installation resolved to 0.17.1.
- Licence: MIT.
- Size: one development-only platform binary; absent from the deployed runtime
  dependency set.
- Platform support: published binaries support common operating systems and
  Python 3.14 syntax.
- Security implications: it reads the owned source tree and can rewrite files
  only when formatting is explicitly requested; continuous integration uses
  read-only check modes.
- Test strategy: lint and format checks run separately on every pull request.
- Replacement cost: medium because rule selection and formatting would need to
  be mapped to replacement tools.

## MyPy

- Behaviour provided: strict static type analysis for the owned Python source.
- Why the standard library or platform is insufficient: Python records type
  annotations but does not statically validate them.
- Maintenance status: active release 2.4.0 was current and installed when
  selected.
- Licence: MIT.
- Size: development-only Python tooling with a platform-specific analysis
  component; absent from the deployed runtime dependency set.
- Platform support: Python 3.10 or later, with declared Python 3.14 support, on
  common operating systems.
- Security implications: it reads project source and imported type information;
  it is not part of the bot runtime and receives no Discord data or secrets.
- Test strategy: strict analysis of the package and repository checker runs on
  every pull request with any diagnostic treated as failure.
- Replacement cost: medium to high because strictness, annotations, and external
  library typing behaviour would need revalidation in another analyser.
