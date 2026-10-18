# Privacy

Krill Bot is an unofficial Discord companion for Krillion, run privately by its
author on servers the author chooses. It is not Krillion's own and shares
nothing with Krillion.

Krill Bot keeps a Discord user ID with each result a player logs. A Discord
user ID is personal data, because it identifies one Discord account.

## What is kept

Krill Bot keeps one SQLite database. These are every table and column in it.

`daily_results`, one row per result a player chose to log:

| Column | What it holds |
|---|---|
| `guild_id` | the Discord server the result was logged in |
| `user_id` | the Discord user ID of the player who logged it |
| `daily_number` | Krillion's daily number, such as 95 |
| `score` | the score copied from Krillion |
| `emoji_row` | the row of round symbols copied from Krillion |
| `logged_at` | when it was logged, in UTC |

`daily_posts`, one row per server that set up a daily post:

| Column | What it holds |
|---|---|
| `guild_id` | the server |
| `channel_id` | the channel or thread the post goes to |
| `clock` | the server's chosen post time, if it chose one |
| `reset_clock` | the server's chosen dive reset time, if it chose one |
| `next_run` | when the next post is due, in UTC |

`guild_settings`, one row per server that changed a setting:

| Column | What it holds |
|---|---|
| `guild_id` | the server |
| `hide_until_logged` | whether `/dive today` hides scores until the viewer has logged |

The log files record which command ran in which server, why a paste was
refused, and how many rows a deletion removed. They never record who ran a
command, what anyone pasted, or a user ID. The logs rotate at 1 MB, and five
old files are kept.

## What is never kept

- Discord names, nicknames or display names
- the text of any message, including the conversation around a pasted result
- message IDs
- Krillion answers, which a copied result does not contain
- anything typed into a command beyond the parsed result fields above

Krill Bot reads no ordinary channel messages. It sees a message only when a
player picks Log Krillion result on their own message, and keeps only the
parsed fields from it.

## Which server owns a row

Every result belongs to the server it was logged in. Boards, streaks and
`/dive me` only ever read one server's rows, and nothing moves between
servers.

## How long rows are kept

Rows are kept until the player deletes them with `/dive forget`, or until
Krill Bot is removed from the server. Nothing is deleted for age. Krill Bot
itself makes no backups.

## Deleting your results

`/dive forget scope:here` deletes your results in the current server.
`/dive forget scope:everywhere` deletes your results in every server. Each
says how many results it will delete and waits for you to press Delete. Only
you can press it, and nothing is deleted if you press Cancel.

## Removing Krill Bot from a server

When Krill Bot is removed from a server, it deletes every result logged
there, the server's daily post and its settings. When a channel or thread
holding a daily post is deleted, that daily post stops.

## What this does not protect against

- The author runs the computer the database lives on, and can read it.
- The database and logs are not encrypted on disk.
- A result posted in a channel stays in Discord, under Discord's own privacy
  policy, whatever Krill Bot does with it.
- Anyone in a server can see its boards, and so which members logged results
  and their scores.
- Backups the author's own machine makes of its disk are outside Krill Bot's
  control.
