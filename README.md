# Krill Bot

Krill Bot is an unofficial Discord scoreboard companion for Krillion. Players
choose to submit the result copied by Krillion; the bot never contacts
krillion.io and never reads ordinary channel messages.

Krill Bot is private: the author adds it to the servers it runs on.

- `/dive log`, or Log Krillion result on your own message, records a result.
- `/dive me`, `/dive today`, `/dive board` and `/dive streak` show results,
  boards and streaks for the current server.
- `/dive forget` deletes your results here or everywhere, after you confirm.
- `/setup visibility`, `/setup show` and `/setup daily` let a server manager
  choose whether today's scores wait until a viewer has logged, and set up a
  daily post with yesterday's board.

What is stored and how to delete it is in `PRIVACY.md`, the trust boundaries
in `SECURITY.md`, the permissions in `docs/DISCORD_LISTING.md`, and the result
grammar's evidence boundary in `CONTRACT.md`.

## Development

The supported runtime is Python 3.14. Install the package and development tools
from inside this directory:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest
```

Use a separate development Discord application and keep its token in
`.env.dev`. The author, not the coding agent, starts the bot against Discord.

This project follows `ENGINEERING_DATUM.md` version 2 and the Krillion Discord
bot specification draft 1, both dated in their source documents.

