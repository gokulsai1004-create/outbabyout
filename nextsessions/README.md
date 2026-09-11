# Next sessions

Two sessions run in parallel. Open a terminal for each, paste the matching prompt,
and leave them in their lanes.

| | Owns | Prompt |
|---|---|---|
| **Engine** | `outbabyout.py`. The match, scoring, the permanent page. No radio, ever. | [`ENGINE-PROMPT.md`](ENGINE-PROMPT.md) |
| **Web** | `index.html`, `play.html`, `field.html`. Everything a person opens. | [`WEB-PROMPT.md`](WEB-PROMPT.md) |
| **Radio** | `ruler.py`, `soak.py`. Closed: the question it existed for is answered. | [`RADIO-PROMPT.md`](RADIO-PROMPT.md) |

Read [`../docs/CONSTRAINTS.md`](../docs/CONSTRAINTS.md) before either. It is the list of
things already tried and already failed, so a session does not spend an hour rediscovering
one of them. Both prompts point at it rather than copying it, so the rules stay in one
place instead of drifting into two.

## Why this split

The line is drawn where two sessions would otherwise collide.

**Engine owns the rules.** It is pure Python with no dependencies and no hardware, so
every rule can be proved by running `--check` on any machine. That is the whole point of
keeping it separate: the part that decides who won must be testable without a Bluetooth
adapter, a phone, or a park.

**Radio owns the physics.** RSSI, thresholds, whether two metres can be told from ten.
It needs a real adapter and a real room, so nothing it produces can be unit tested the
same way. It uses `bleak`, which the engine must never import.

A tag that the radio detects becomes **a line of text**. That is the entire interface
between them. If the radio session finds itself editing scoring, or the engine session
finds itself reading dBm, the line has been crossed.

## Before you paste

- Every session commits after every change. **Push only when Gokul says so.** On this
  project he asks for pushes often, because the pages have to be live to be tested at
  all, so a requested push is normal here and a silent one is not.
- Update the "current state" line in each prompt when it goes stale. A prompt that claims
  nine commits when there are sixteen teaches the session that the file is not to be
  trusted. This has already happened once on this repo, which is why it is written twice.
- If a session learns something that cost it more than twenty minutes, it adds a line to
  `docs/CONSTRAINTS.md` before finishing. That file is the reason the next session is
  faster than this one.
