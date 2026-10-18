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
4. one whitespace-free round row, preserved exactly as supplied

Only the daily number, score, emoji row, recognised-symbol subtotal, whether the
whole row is recognised, and conservative score-check result may leave the
parser. Conversation surrounding the block is never returned.

## Current limits

The parser refuses input over 2,000 characters before matching it. It refuses
text containing no complete block and text containing several complete blocks.
A row made entirely from known symbols must still contain exactly seven symbols.
Any row containing an unknown symbol is treated as opaque because Python's
standard library cannot reliably split every composed emoji into display
characters.

The parser adds the points for every recognised symbol. A score is marked as
matching only when the entire row is recognised and its total equals the copied
score. Unknown symbols and score mismatches are accepted so a new game symbol
does not prevent logging during the update lead time.

Unlimited, Archive, and pack result markers are not known, so they cannot yet
receive the more specific `not-daily` rejection. The daily reset and number to
date mapping are also unknown, so `from-the-future` is not implemented. Genuine
fixtures are required before either rule is added.
