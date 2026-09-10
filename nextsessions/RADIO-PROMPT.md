# Out Baby Out — radio session

You own `ruler.py` and `soak.py`. The engine session owns `outbabyout.py` and the scoring.
Do not edit those. A tag you detect becomes **one line of text** in a match log; that is
the entire interface between the two halves.

## Read first

`docs/CONSTRAINTS.md`, in full, before touching anything. The Bluetooth section is
measured, not assumed, and it already rules out the obvious design.

## Current state, 10 Sept 2026

`ruler.py` scans, tracks one device live, samples at a marked distance into `rssi.json`,
and gives a verdict on whether near and far separate. `soak.py` runs unattended for ten
minutes against two fixed ceiling-fan beacons.

Measured so far, laptop and beacon both **stationary**:

- ten readings spanned **24 dBm** (min −74, max −50, stdev 7.7)
- twelve samples tightened the standard error of the median to **1.1 dBm**
- two beacons at different distances separated by **12 dBm at the median**, while their
  **raw ranges still overlapped**

*(If this no longer matches `soak.json` and `rssi.json`, fix this paragraph first.)*

## The question you exist to answer

**Can a tag be called correctly?** Not "does Bluetooth work" — whether a rule can fire at
two metres and not at ten, with a phone in a pocket and a body in the way.

The answer so far is: **not from one reading**. The noise with nothing moving is about
four doublings of distance. So the real question has moved on to:

> How many readings, over how many seconds, does a tag need before it is right often
> enough to play with?

That is a number. Go and get it.

## What is next, in order

1. **Finish the distance curve.** Tape marks at 1, 2, 5, 10 m; `--sample` at each; then
   **2 m again with the phone in a pocket and a body in the way**. That last one decides
   it. `--verdict` already reports whether the ranges separate.
2. **Then the one that matters more: do phones advertise at all?** A plain scan of this
   room found ceiling fans, not phones. Phones rotate their Bluetooth address and do not
   advertise continuously in the background without an app deliberately doing it.
   **Establish this properly.** If a phone cannot be a reliable beacon in the background,
   the design changes completely and no amount of RSSI work matters. This is the highest
   value thing in the repo right now.
3. **Only then**, a threshold: N readings within T seconds, median above X. Report its
   false-positive and false-negative rate against tape marks, not a guess.

## Constraints not to rediscover

- A powered-off radio **raises**; `scan()` converts it to `Blocked` and `main()` exits 2.
  Never catch it into an empty list. An adapter that never ran must not print as a quiet
  room — that is the bug this whole project exists to avoid.
- A device never seen during a sample is **not recorded**. An unseen device is not a weak
  reading; saving it as one would drag the median and fake the verdict.
- `bleak` has no `__version__`. That AttributeError is not a broken install.
- `rssi.json` that will not parse is BLOCKED, not an empty experiment. Returning `{}`
  would silently discard every measurement taken so far and print a verdict from nothing.
- `bleak` stays on this side. The engine has no dependencies and must keep none.

## How this session works

- Every claim is a measurement with an n, a median and a spread. No "it seems to".
- Anything measured goes into `docs/CONSTRAINTS.md` as a fact with its date, so the next
  session does not repeat the experiment.
- **Commit after every change. Never push.** Gokul pushes.
