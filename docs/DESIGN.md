# Design

One look across everything: the rules page, the match page, and whatever the app
becomes. Decided 11 Sept 2026 and not up for renegotiation per-screen — a session
that wants a different palette for its own screen is wrong.

## Why it looks like this

A floodlit ground at night. Dark, high contrast, one acid colour that does not
appear in nature. It has to be readable on a phone held at arm's length in
daylight, and it has to not read as a children's game — that was the first
version's failure and the reason this file exists.

## Colour

| Token | Hex | Used for |
|---|---|---|
| `--field` | `#0F1310` | the page ground |
| `--panel` | `#191E17` | anything raised off it — cards, code blocks |
| `--chalk` | `#F2F4E9` | body text |
| `--dim` | `#8C9682` | secondary text, labels, captions |
| `--line` | `#2C352A` | borders and rules |
| `--vish` | `#E0523B` | **frozen.** Only ever means caught or blocked |
| `--amrit` | `#5FD08A` | **revived.** Only ever means freed or verified |
| `--hot` | `#E8FF3F` | the one accent. Headline, the winning number, links |

**Vish and amrit are semantic, not decorative.** Red means someone went down.
Green means someone came back. Never use either for emphasis, a heading, or a
button — the moment red means two things, the timeline stops being readable at a
glance.

**`--hot` is spent once per screen.** The page title, or the winning score, or a
link. Not all three in the same eyeline.

Single theme. It commits to the floodlit look rather than trying to work in light
mode, so every colour is set explicitly and nothing is inherited from the host.

## Type

| Role | Face | Fallback |
|---|---|---|
| Display | **Anton**, uppercase, tight leading | `Impact, sans-serif` |
| Body | **Instrument Sans** | `"Segoe UI", system-ui, sans-serif` |
| Data, labels, code | **JetBrains Mono** | `ui-monospace, Consolas, monospace` |

Every number a person might compare to another number is set in mono with
`tabular-nums`. Scores, times, dBm, counts. A figure in a proportional face reads
as a claim; the same figure in mono reads as a measurement, and nearly everything
this project prints is a measurement.

Labels above a block are mono, uppercase, `letter-spacing: .09em`, in `--dim`.

## Rules

- Nothing animates. There is no state worth a transition here.
- A card gets a border, not a shadow. Shadows on a dark ground turn to mud.
- Wide things scroll inside their own container. The page body never scrolls sideways.
- Print, where it exists, swaps to system faces on white. A PDF that references a
  web font it never loaded gets substituted with whatever the reader has.
