# Notes

## What playing found

- **The computer's hand was empty while mine still had two cards.** I first
  suspected a bug. It is not one, it follows from the rules the module plays:
  - The tests allow capturing with a *combination* of hand cards, and the
    computer used that: in one move it played three hand cards (10D, 4H, 7S)
    and took two table cards, so its hand ran out faster than mine.
  - After a sweep the opponent moves twice in a row (required by
    `test_sweep_and_the_double_move_after_it`), which also unbalances how many
    cards each player has left.
  - When one player has no cards and the other still does, the player with
    cards keeps playing. Once both hands are empty, the last player to capture
    draws three cards, deals three to the opponent and leads.
- **The log was hard to follow.** The server only sent the last 12 lines and the
  page showed them in a plain list, so a longer deal lost its history and the
  newest line could be out of view.

## What I asked the agent to change

1. **Build a casino game** whose module passes the tests in `tests/`.
   The agent wrote `casino.py`, plus a computer opponent (`computer.py`) and a
   browser table (`server.py`, `static/index.html`) because the README asks for
   both.
2. **Make the log scrollable at the bottom.** The server now sends the whole
   log of the deal, and the log box has a fixed height, scrolls, and jumps to
   the newest line after every update.
3. **Explain the empty computer hand** (see above), and **write these notes.**

## Rule choices the tests did not decide

These were the agent's decisions, so they are worth checking against the rules
you want:

- Card values are A=1 … K=13 (the ace is never 14).
- A capture may take several groups of table cards, as long as each group adds
  up to the total of the hand cards played.
- Sweeping with the last card of the deal scores nothing.
- If nobody captured all deal, the cards left on the table go to the player who
  made the last move.
