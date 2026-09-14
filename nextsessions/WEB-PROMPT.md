# Out Baby Out — web session

You own `index.html`, `play.html` and `field.html`. The engine session owns
`outbabyout.py`, the radio session owns `ruler.py` and `soak.py`. Do not edit theirs.

## Read first

- `docs/DESIGN.md` — the look is fixed and is not renegotiated per screen.
- `docs/CONSTRAINTS.md` — things already tried and already failed.

## Current state, 11 Sept 2026

Three pages, all live at **https://vgokulsai.github.io/outbabyout/** and all
linked to each other. No build step, no framework, no bundler. Leaflet is the only
external script and it comes from cdnjs.

| page | what it is |
|---|---|
| `index.html` | the rules. Written to be read in ninety seconds on a phone in sunlight |
| `play.html` | the live match console. Two taps a move, rules enforced, log out at the end |
| `field.html` | the field map. Boundary, two starts, whole setup in the URL hash |

`play.html` reads `#n=`, `#t1=` and `#t2=` so `field.html` can hand it the venue and the
team names. It has a demo button that runs six real moves through the same code path
with twenty one seconds on the clock.

**The rules live in `<script id="rules">`, alone, with no DOM in it.** That block is the
single copy of the match rules on the web side, and `tests/test_agree.py` lifts it
verbatim out of this file and runs it in node against `outbabyout.py`. Keep it pure: the
test asserts it never touches `document.` or `window.`, because the moment it does it
stops being testable and the two implementations can drift apart unnoticed.

*(If that no longer matches the repo, fix this paragraph before anything else. A prompt
that lies about the state teaches the session that this file is not to be trusted. It has
already gone stale once, between commit nine and commit sixteen.)*

## Rules of these pages

- **Verify on the deployed URL, not locally.** A local file and a GitHub Pages URL are
  different origins with different caches, and the CARTO watermark got through a local
  check and was caught by a real phone. Push, wait for the build, then look.
- **No player positions on the map. Ever.** Not a setting, not a toggle, absent. Every
  incumbent in this category died on live location. The map shows the boundary and where
  each side starts, agreed before the whistle.
- **Nothing is sent anywhere and nothing is stored.** No account, no analytics, no
  database. State lives in the URL hash or nowhere. Keep it that way: the entire user base
  is under eighteen and collecting their data would be a legal obligation neither founder
  can carry.
- **A refused move says why.** Tapping a frozen player answers with the reason, not with
  silence and not by recording it anyway. That is the same rule the Python engine
  enforces, moved to where the mistake actually happens.
- **Every third-party URL is checked for whether it needs a key**, and the answer goes in
  `docs/CONSTRAINTS.md` with the date.

## What is next

Nothing, until a match is played. The pages are finished for the test the council set.
Do not add features to this while the verdict is waiting on ten people in a park.

When that test comes back, the first real thing is a **session page**: three or four
back-to-back matches with a running table, because a league needs standings and one match
page cannot hold them.

## How this session works

- **Commit after every change.** Push only when Gokul says so; he has been asking for
  pushes on this project because the pages have to be live to be tested, so treat a push
  as normal here and a silent push as not.
- Check the JavaScript parses before committing: extract the script block and run
  `node --check`. There is no build step to catch a syntax error for you.
- Run `py -3 -m pytest tests/ -q` before committing a rule change. Twelve tests check
  that this page and the Python scorer still agree, and they fail if you change one
  side without the other.
- If something costs more than twenty minutes, add a line to `docs/CONSTRAINTS.md`.
