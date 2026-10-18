# Changelog

## Unreleased

- Began KE1 with the Python package skeleton, validated configuration, versioned
  SQLite schema, Discord client, `/help`, privacy-safe logging, repository policy
  checks, continuous integration, and systemd service.
- Added the datum 0.13 record for every runtime and development dependency.
- Added the author-selected MIT licence under TheScottBot.
- Added the known daily-result grammar, bearing calculation, six real fixtures,
  parser fuzz properties, and an explicit contract record.
- Allowed new round emoji without rejecting a result while retaining a
  conservative subtotal and full-row validation signal.
- Added server-scoped result storage, `/dive log`, `/dive me`, and the
  author-only Log Krillion result message menu.
- Replaced the proposed aggregate format-change warning with private guidance
  on each unrecognised paste, as selected by the author.
- Added pure rolling board aggregation and current and longest streak
  calculations.
- Added hidden daily boards, rolling server boards, streak commands, and private
  multi-message paging with mentions disabled.
- Showed each score's bearing on `/dive today`, kept every board page and
  result history inside Discord's limits with a truncation note, made board
  averages exact for scores of any size, and widened the displayed-string check
  to composed text and command descriptions.
- Added `/setup visibility` and `/setup show`, each requiring Manage Server and
  replying privately.
- Recorded what Python offers for memory and undefined behaviour analysis, and
  ran the whole suite under development mode with warnings as errors in
  continuous integration.
- Added the daily post: per-server post and reset times with environment
  fallbacks of 17:00 and 04:00, `/setup daily here`, `stop` and `show`,
  yesterday's board, a six-hour grace period, and a one-minute loop that
  always moves each post on to its next day.
