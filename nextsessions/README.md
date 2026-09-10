# Next sessions

Two sessions run in parallel. Open a terminal for each, paste the matching prompt,
and leave them in their lanes.

| | Owns | Prompt |
|---|---|---|
| **Engine** | The match, scoring, the permanent page. No radio, ever. | [`ENGINE-PROMPT.md`](ENGINE-PROMPT.md) |
| **Radio** | Bluetooth, measurement, whether a tag can be called at all. | [`RADIO-PROMPT.md`](RADIO-PROMPT.md) |

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

- Both sessions commit after every change and **never push**. Gokul pushes.
- Update the "current state" line in each prompt when it goes stale. A prompt that claims
  two commits when there are nine teaches the session that the file is not to be trusted.
- If a session learns something that cost it more than twenty minutes, it adds a line to
  `docs/CONSTRAINTS.md` before finishing. That file is the reason the next session is
  faster than this one.
