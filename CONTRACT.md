# Result grammar contract

The executable contract is the single grammar table and parser in
`krillbot/result_grammar.py`. Its real examples are stored without surrounding
conversation in `tests/samples/`.

## Evidence

The six initial samples were supplied by the author on 18 October 2026. They
cover daily numbers 93 through 95, scores from 150 through 435, and the five
symbols ⬛, 🫧, 🐟, 🦑, and 🏮. The author later observed the current round labels
and values for every symbol except 🐟 while playing on the same date.

The parser accepts one four-line daily block inside optional surrounding text:

1. `Krillion #`, a positive daily number, a space, and 🦐
2. a non-negative decimal score with no leading zeroes
3. a blank line
4. exactly seven known round symbols

Only the daily number, score, emoji row, and whether the score matches the
inferred row total may leave the parser. Conversation surrounding the block is
never returned.

## Current limits

The parser refuses input over 2,000 characters before matching it. It refuses
text containing no complete known block and text containing several complete
blocks. Unknown symbols and malformed blocks are rejected as `not-a-result`.

Score and row mismatches are accepted and marked because the point values are
observed or inferred rather than a published interface. They are not yet a
rejection reason.

Unlimited, Archive, and pack result markers are not known, so they cannot yet
receive the more specific `not-daily` rejection. The daily reset and number to
date mapping are also unknown, so `from-the-future` is not implemented. Genuine
fixtures are required before either rule is added.
