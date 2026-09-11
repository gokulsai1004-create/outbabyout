# Out Baby Out — engine session

You own `outbabyout.py`, `docs/` and the tests. The radio session owns `ruler.py` and
`soak.py`. Do not touch those, and do not import `bleak` — the engine must stay provable
on a machine with no Bluetooth adapter.

## Read first

- `docs/CONSTRAINTS.md` — things already tried and already failed. Especially the heredoc
  trap, which has broken this repo four times.
- `README.md` — what the tool refuses and why.

## Current state, 11 Sept 2026 — PAUSED

**Nine commits, all pushed, working tree clean.** Paused deliberately while Gokul and
Dhrishaj start the opportunity-agent build; this is not abandoned and the next step is
known. Live rules page: https://gokulsai1004-create.github.io/outbabyout/

`py -3 outbabyout.py --check` passes: the example match end to end plus **eleven
refusals** — unknown player, player on two teams, tagging a teammate, reviving an enemy,
a frozen player acting, double-freezing, reviving someone not frozen, events out of
order, a tag after full time, a line it cannot parse, and acting on yourself. Verified by
removing a refusal and confirming the check fails. `--html` writes the match page, which
leads with the result and draws one pip per player.

`metrics()` reports the three thresholds the council fixed before any match was played:
late tags against early tags, mean frozen time, longest stretch with nothing happening.
Proved against a synthetic stalling log, which fails two of the three.

*(If that paragraph no longer matches the repo, fix the paragraph first. A prompt that
lies about the state teaches the session that this file is not to be trusted.)*

## The verdict this is paused under

A five-persona council ruled **PIVOT at 66%** on 11 Sept 2026. Full fight at
`~/.council/out-baby-out/council-2026-09-11.md`; assumptions ledger beside it.

The pivot: stop building a rules page and a scorer for other groups to adopt, and build a
recurring fixed-time league in one Hyderabad park with persistent standings, where this
engine is private plumbing rather than software anyone installs. Every persona, including
the one arguing in favour, asked the same question: does a second and third game happen
without him.

**Nothing here moves that verdict. Only a played match does.** Do not add features hoping
to improve the odds.

## The game

Two teams, a timer. A tag freezes you — **vish**. A teammate reaching you brings you back
— **amrit**. Most players standing when the clock runs out wins.

The revive is the product. Every competitor is last-human-standing, which means the second
half of every match is a formality. Do not add a mode that removes it.

## What is next, in order

**Step one is not code.** One session in one park, ten people, no app, tags called out
loud, two back-to-back twenty minute matches with the same teams. Gokul logs match one;
for match two he hands the phone to a player and does not coach them. Then he says nothing
about a next game for seven days. The rules card, the engine and the thresholds are all
finished and waiting on that.

Pass marks, fixed in advance and not to be loosened afterwards:

- **Format** — `--check` output says ok on all three: late tags at least half the early
  tags, mean freeze at least ten seconds, no quiet stretch over three minutes.
- **Retention** — within seven days, unprompted, at least four of the ten ask when the
  next one is, and at least one offers to run it.
- **Scoring** — the match two log, written by somebody else, is accepted first try with no
  edits, and at least three people ask what the score was.

Then, and only then:

1. **A session page.** Three or four back-to-back matches with a running table, because a
   league needs standings and a single match page cannot hold them. This is the first
   thing the pivot actually requires.
2. **Zones.** A match happens inside a named area; the log should say which. A name is
   probably enough until a real game says otherwise.
3. **Do not build a phone app.** RSSI is ruled out and measured; a QR or NFC tag needs
   accounts, a server, live shared state and anti-cheat, which the council called a year
   disguised as a weekend. The first hundred matches need no app at all.

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
