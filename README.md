# Krill Bot

Krill Bot is an unofficial Discord scoreboard companion for Krillion. Players
choose to submit the result copied by Krillion; the bot never contacts
krillion.io and never reads ordinary channel messages.

The project is in its first implementation phase. The result grammar, boards,
daily posting, deletion controls, and public documents will be added only in
their specification phases.

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

