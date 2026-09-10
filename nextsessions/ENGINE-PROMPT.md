# Out Baby Out — engine session

You own `outbabyout.py`, `docs/` and the tests. The radio session owns `ruler.py` and
`soak.py`. Do not touch those, and do not import `bleak` — the engine must stay provable
on a machine with no Bluetooth adapter.

## Read first

- `docs/CONSTRAINTS.md` — things already tried and already failed. Especially the heredoc
  trap, which has broken this repo four times.
- `README.md` — what the tool refuses and why.

## Current state, 10 Sept 2026

Three commits. `py -3 outbabyout.py --check` passes: it covers the example match end to
end plus **eleven refusals** — unknown player, player on two teams, tagging a teammate,
reviving an enemy, a frozen player acting, double-freezing, reviving someone not frozen,
events out of order, a tag after full time, a line it cannot parse, and acting on
yourself. The self-check was verified by removing a refusal and confirming the check
fails. `--html` writes the permanent match page.

*(If that paragraph no longer matches the repo, fix the paragraph first. A prompt that
lies about the state teaches the session that this file is not to be trusted.)*

## The game

Two teams, a timer. A tag freezes you — **vish**. A teammate reaching you brings you back
— **amrit**. Most players standing when the clock runs out wins.

The revive is the product. Every competitor is last-human-standing, which means the second
half of every match is a formality. Do not add a mode that removes it.

## What is next, in order

1. **Zones.** A match happens inside a named area; the log should be able to say which.
   Decide whether a zone is a name only or has a boundary — a name is probably enough
   until a real game says otherwise.
2. **A rules card.** One page, printable or sendable on WhatsApp, that ten people can read
   in ninety seconds and then play. This is what unblocks the first real game, and the
   first real game is what decides whether any of the rest matters.
3. **Multiple matches on one page.** A session of three or four back-to-back games, with a
   running table. Every match already gets a permanent page; a night of them should too.
4. **Do not build a phone app.** The radio session is still measuring whether a tag can be
   detected at all. Until it says yes, an app is a guess.

## Constraints not to rediscover

- The log format is written **by a human, during a game, on a phone, in a hurry**. Every
  change to it must survive that. No JSON, no required fields that a person would forget.
- `parse()` raises `Bad` rather than skipping a line it cannot read. A match that scores
  3–2 because two lines were unparseable looks exactly like a match that was 3–2. Do not
  add a "lenient" mode.
- Times in a log are minutes into the match, not clock time. People do not know the wall
  time when they are running.
- The HTML page is a single self-contained file with the palette inline. It must render
  from `file://` with no server and no network.

## How this session works

- `py -3 outbabyout.py --check` after every change. Keep it green.
- When you add a rule, add its refusal to the self-check, then **prove the check bites**:
  remove the rule, confirm the check fails, put it back.
- **Commit after every change. Never push.** Gokul pushes.
- If something costs you more than twenty minutes, add a line to `docs/CONSTRAINTS.md`
  before you finish.
