# Security

Krill Bot is a private Discord bot. It runs as a long-lived process holding a
Discord bot token, keeps one SQLite database, and never contacts krillion.io.

## Trust boundary: pasted result text

The result text a player pastes, or the message they pick from the menu, is
the only untrusted input that carries meaning.

- It is refused above 2,000 characters before it is read.
- The parser in `krillbot/result_grammar.py` matches one complete result block
  and returns only its parsed fields, or one stable rejection reason.
- Text around the block is never stored, logged or echoed back.
- The parser is pure Python with no storage or network access, checked by an
  import test, and fuzzed with Hypothesis in continuous integration.

## Trust boundary: Discord interaction payloads

Every command, button press and menu choice arrives as a Discord interaction.

- `/setup` commands check Manage Server when used, not only through Discord's
  default command permissions, which a server can widen.
- The Log Krillion result menu refuses a message written by anyone other than
  the person using it.
- The `/dive forget` buttons refuse anyone other than the person who ran it.
- Every query is scoped to the server the interaction came from, except
  forgetting everywhere, which deletes by the caller's own user ID.
- Every message is sent with mentions disabled, so nothing the bot sends can
  ping anyone.
- Krill Bot uses Discord's default intents and does not request the message
  content intent.

## Secrets and the host

- The bot token lives only in `.env` or `.env.dev`, which are never committed.
- The systemd service runs as its own user with `NoNewPrivileges`,
  `ProtectSystem=strict`, `ProtectHome` and `PrivateTmp`, and may write only
  below `/opt/krillbot`.
- The bot requests only Send Messages, Embed Links and Send Messages in
  Threads, as `docs/DISCORD_LISTING.md` records.

## Accepted risks

- A pasted score is not proven genuine. Anyone can edit a copied result before
  logging it, and the bot accepts scores its known round values do not
  explain, so that a new Krillion symbol does not stop logging.
- Round symbols the bot does not recognise are accepted and stored as pasted.
- Discord user IDs are stored with scores, as `PRIVACY.md` describes.
- The database and logs are unencrypted on the host.

## Limitations

- Pure Python offers no sanitiser for the bot's own code; `TESTING.md` records
  what development mode covers instead.
- Live Discord behaviour, including permission checks and button handling,
  is tested against doubles, not Discord itself, until the author's KE8 checks.
- A Discord server administrator can always remove the bot or change who may
  run its commands; the runtime checks still apply.
