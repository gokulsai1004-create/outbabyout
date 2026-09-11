"""A match of real-life tag, scored from a log a human can write during it.

Two teams, a timer. You freeze someone by getting close to them - vish. A
teammate who reaches them brings them back - amrit. Whoever has more players
standing when the timer ends wins.

The revive is the whole point. Straight infection has no way back, so the
second half of every match is a formality and the losing team goes home. Vish
Amrit is the game Indian kids already play, and it makes the timer matter.

The log is plain text on purpose. The first games will be played with no app
at all - ten people in a park, tags called out loud, someone writing lines on
their phone. This reads that. It will read a phone's output later without
changing, because the format is the same either way.

    py -3 outbabyout.py match.txt          score it
    py -3 outbabyout.py match.txt --html   also write match.html
    py -3 outbabyout.py --example          write an example log to start from
    py -3 outbabyout.py --check            run the self-check

A log looks like this:

    # Gachibowli, 13 Sept
    LENGTH 20:00

    RED   gokul, arjun, sai
    BLUE  daniel, priya, rahul

    02:14  gokul > priya
    03:40  daniel + priya

`>` is a tag, `+` is an amrit. Nothing else is a line.
"""

import argparse
import html
import io
import os
import re
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

TAG, CURE = ">", "+"

CLOCK = re.compile(r"^(\d{1,3}):([0-5]\d)$")
EVENT = re.compile(r"^(\d{1,3}:[0-5]\d)\s+(.+?)\s*([>+])\s*(.+?)$")
TEAM = re.compile(r"^([A-Z][A-Z0-9_]*)\s+(.+)$")


class Bad(Exception):
    """A log line that could not be read.

    Raised rather than skipped. A line nobody could parse must never quietly
    shrink the scoreboard - a match that scores 3-2 because two tags were
    unreadable looks exactly like a match that really was 3-2.
    """


def seconds(text):
    m = CLOCK.match(text.strip())
    if not m:
        raise Bad("%r is not a time like 12:30" % text)
    return int(m.group(1)) * 60 + int(m.group(2))


def clock(total):
    return "%d:%02d" % (total // 60, total % 60)


def label_of(text):
    """The first comment line, which is where people write the place.

    `# Gachibowli, Saturday` is what someone types at the top of a log without
    being asked to. A filename is what the computer happened to call it.
    """
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
        if line:
            return ""
    return ""


def parse(text):
    """(length, {team: [players]}, [events]). Raises Bad, never guesses."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    length, teams, events = None, {}, []
    seen = {}

    for number, raw in enumerate(text.split("\n"), 1):
        line = raw.split("#")[0].strip()
        if not line:
            continue
        try:
            if line.upper().startswith("LENGTH"):
                if length is not None:
                    raise Bad("LENGTH given twice")
                length = seconds(line[6:])
                continue

            event = EVENT.match(line)
            if event:
                at, actor, mark, target = event.groups()
                events.append({
                    "at": seconds(at), "actor": actor.strip().lower(),
                    "mark": mark, "target": target.strip().lower(),
                    "line": number,
                })
                continue

            team = TEAM.match(line)
            if team:
                name = team.group(1)
                if name in teams:
                    raise Bad("team %s listed twice" % name)
                members = [p.strip().lower() for p in team.group(2).split(",")
                           if p.strip()]
                if not members:
                    raise Bad("team %s has nobody in it" % name)
                for player in members:
                    if player in seen:
                        raise Bad("%s is in both %s and %s"
                                  % (player, seen[player], name))
                    seen[player] = name
                teams[name] = members
                continue

            raise Bad("not a team, a LENGTH, or an event: %r" % line)
        except Bad as exc:
            raise Bad("line %d: %s" % (number, exc))

    if length is None:
        raise Bad("no LENGTH line - how long was the match?")
    if len(teams) < 2:
        raise Bad("need at least two teams, found %d" % len(teams))
    return length, teams, events


def play(length, teams, events):
    """Run the match. Returns (frozen set, [tree rows]).

    Every rule violation raises. An impossible event is a mistake in the log
    or a disputed call on the day, and either way somebody has to look at it -
    silently dropping it would move the score.
    """
    side = {p: name for name, members in teams.items() for p in members}
    frozen, tree, last = set(), [], -1

    for e in events:
        where = "line %d" % e["line"]
        if e["at"] < last:
            raise Bad("%s: %s is earlier than the event before it"
                      % (where, clock(e["at"])))
        if e["at"] > length:
            raise Bad("%s: %s is after the match ended at %s"
                      % (where, clock(e["at"]), clock(length)))
        last = e["at"]

        for who in (e["actor"], e["target"]):
            if who not in side:
                raise Bad("%s: %r is not on any team" % (where, who))
        if e["actor"] == e["target"]:
            raise Bad("%s: %s cannot act on themselves" % (where, e["actor"]))
        if e["actor"] in frozen:
            raise Bad("%s: %s is frozen and cannot act"
                      % (where, e["actor"]))

        same = side[e["actor"]] == side[e["target"]]
        if e["mark"] == TAG:
            if same:
                raise Bad("%s: %s and %s are both %s - you cannot tag your own"
                          % (where, e["actor"], e["target"], side[e["actor"]]))
            if e["target"] in frozen:
                raise Bad("%s: %s is already frozen" % (where, e["target"]))
            frozen.add(e["target"])
        else:
            if not same:
                raise Bad("%s: %s cannot revive %s - different teams"
                          % (where, e["actor"], e["target"]))
            if e["target"] not in frozen:
                raise Bad("%s: %s is not frozen" % (where, e["target"]))
            frozen.discard(e["target"])

        tree.append({"at": e["at"], "actor": e["actor"], "mark": e["mark"],
                     "target": e["target"], "team": side[e["actor"]]})

    return frozen, tree


def score(teams, frozen):
    """[(team, standing, total)], best first."""
    rows = [(name, sum(1 for p in members if p not in frozen), len(members))
            for name, members in teams.items()]
    return sorted(rows, key=lambda r: (-r[1], r[0]))


def report(length, teams, frozen, tree):
    rows = score(teams, frozen)
    out = ["", "  %s match, %d players" % (clock(length),
                                           sum(len(m) for m in teams.values()))]
    out.append("  " + "-" * 56)
    for name, standing, total in rows:
        bar = "#" * standing + "." * (total - standing)
        out.append("  %-8s %2d of %-2d  %s" % (name, standing, total, bar))

    top = rows[0][1]
    winners = [n for n, s, _ in rows if s == top]
    out.append("")
    if len(winners) > 1:
        out.append("  Drawn on %d each: %s" % (top, ", ".join(winners)))
    else:
        out.append("  %s wins, %d standing." % (winners[0], top))

    tags = sum(1 for t in tree if t["mark"] == TAG)
    cures = len(tree) - tags
    out.append("  %d tags, %d amrits." % (tags, cures))
    if cures:
        out.append("  The amrits are why it was still a game at the end.")
    out.append("")
    return "\n".join(out)


# The look is fixed in docs/DESIGN.md and is the same on every screen. Vish red
# and amrit green are semantic here: red only ever means caught, green only ever
# means brought back. Do not reuse either for emphasis.
PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap">
<style>
:root{--field:#0F1310;--panel:#191E17;--chalk:#F2F4E9;--dim:#8C9682;
--line:#2C352A;--vish:#E0523B;--amrit:#5FD08A;--hot:#E8FF3F;}
*{box-sizing:border-box;}
body{background:var(--field);color:var(--chalk);margin:0;
font:400 17px/1.6 "Instrument Sans","Segoe UI",system-ui,sans-serif;
padding:clamp(1.6rem,5vw,3rem) clamp(1rem,4vw,2rem) 4rem;
-webkit-font-smoothing:antialiased;}
.wrap{max-width:42rem;margin:0 auto;}
h1{font:400 clamp(2.6rem,11vw,4.4rem)/0.85 Anton,Impact,sans-serif;
text-transform:uppercase;color:var(--hot);margin:0 0 .5rem;letter-spacing:.005em;}
.sub{color:var(--dim);margin:0 0 2.4rem;
font:400 .8rem/1.5 "JetBrains Mono",ui-monospace,Consolas,monospace;
letter-spacing:.06em;text-transform:uppercase;}
.score{display:grid;grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));
gap:1rem;margin:0 0 1.6rem;}
.team{border:2px solid var(--line);border-radius:5px;background:var(--panel);
padding:1rem 1.1rem;display:flex;flex-direction:column;gap:.6rem;}
.team b{display:block;color:var(--dim);font-weight:700;
font:700 .72rem/1 "JetBrains Mono",ui-monospace,Consolas,monospace;
letter-spacing:.11em;text-transform:uppercase;}
.n{font:400 3rem/1 Anton,Impact,sans-serif;font-variant-numeric:tabular-nums;}
.n span{font-size:1.1rem;color:var(--dim);}
.team.won{border-color:var(--hot);} .team.won .n{color:var(--hot);}
/* One pip per player: upright in amrit green, on the floor in vish red. The
   final state of the field, readable without counting. */
.pips{display:flex;flex-wrap:wrap;gap:.34rem;}
.pip{width:.62rem;height:.62rem;border-radius:50%%;background:var(--amrit);}
.pip.down{background:var(--vish);}
.who{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));
gap:.9rem;margin:0 0 2.4rem;}
.stat{border-left:3px solid var(--line);padding:.1rem 0 .1rem 1rem;}
.stat.v{border-color:var(--vish);} .stat.a{border-color:var(--amrit);}
.stat em{display:block;font-style:normal;color:var(--dim);
font:700 .68rem/1.5 "JetBrains Mono",ui-monospace,Consolas,monospace;
letter-spacing:.1em;text-transform:uppercase;}
.stat strong{font-size:1.06rem;font-weight:600;}
h2{font:400 1.3rem/1 Anton,Impact,sans-serif;text-transform:uppercase;
letter-spacing:.02em;margin:0 0 .9rem;}
table{width:100%%;border-collapse:collapse;font-size:.97rem;}
td{padding:.55rem .7rem .55rem 0;border-bottom:1px solid var(--line);
vertical-align:top;}
td.t{font:400 .86rem/1.6 "JetBrains Mono",ui-monospace,Consolas,monospace;
font-variant-numeric:tabular-nums;color:var(--dim);width:4.6rem;}
td b{font-weight:600;}
.tag{color:var(--vish);}.cure{color:var(--amrit);}
.scroll{overflow-x:auto;}
footer{margin-top:2.6rem;border-top:1px solid var(--line);padding-top:1.2rem;
color:var(--dim);font-size:.9rem;}
</style></head><body>
<div class="wrap">
<h1>%(verdict)s</h1>
<p class="sub">%(sub)s</p>
<div class="score">%(cards)s</div>
<div class="who">%(stats)s</div>
<h2>Every catch, in order</h2>
<div class="scroll"><table>%(rows)s</table></div>
<footer>%(foot)s</footer>
</div>
</body></html>
"""


def best(tree, mark):
    """(name, count) for whoever did the most of one thing, or None on a tie
    at the top. A shared record is not a record."""
    tally = {}
    for t in tree:
        if t["mark"] == mark:
            tally[t["actor"]] = tally.get(t["actor"], 0) + 1
    if not tally:
        return None
    high = max(tally.values())
    leaders = sorted(n for n, c in tally.items() if c == high)
    return (leaders[0], high) if len(leaders) == 1 else None


def page(title, length, teams, frozen, tree):
    rows = score(teams, frozen)
    top = rows[0][1]
    winners = [n for n, s, _ in rows if s == top]

    # The headline is the result, not the filename. A page about a match that
    # leads with the word "match" has wasted the only line anyone reads.
    if len(winners) > 1:
        verdict = "Drawn %s" % "&ndash;".join(str(s) for _, s, _ in rows)
    else:
        verdict = "%s wins" % winners[0]

    cards = []
    for name, standing, total in rows:
        pips = "".join('<span class="pip%s"></span>' % ("" if i < standing
                                                        else " down")
                       for i in range(total))
        cards.append('<div class="team %s"><b>%s</b>'
                     '<div class="n">%d<span>/%d</span></div>'
                     '<div class="pips">%s</div></div>'
                     % ("won" if standing == top and len(winners) == 1 else "",
                        html.escape(name), standing, total, pips))
    cards = "".join(cards)

    hunter, medic = best(tree, TAG), best(tree, CURE)
    stats = []
    if hunter:
        stats.append('<div class="stat v"><em>Most caught</em>'
                     '<strong>%s &mdash; %d</strong></div>'
                     % (html.escape(hunter[0]), hunter[1]))
    if medic:
        stats.append('<div class="stat a"><em>Pulled the most off the floor</em>'
                     '<strong>%s &mdash; %d</strong></div>'
                     % (html.escape(medic[0]), medic[1]))
    stats = "".join(stats)

    lines = []
    for t in tree:
        verb = "caught" if t["mark"] == TAG else "brought back"
        css = "tag" if t["mark"] == TAG else "cure"
        lines.append('<tr><td class="t">%s</td><td><b>%s</b> '
                     '<span class="%s">%s</span> <b>%s</b></td></tr>'
                     % (clock(t["at"]), html.escape(t["actor"]), css, verb,
                        html.escape(t["target"])))
    if not lines:
        lines.append('<tr><td colspan="2">Nobody was ever tagged.</td></tr>')

    tags = sum(1 for t in tree if t["mark"] == TAG)
    return PAGE % {
        "title": html.escape(title),
        "verdict": verdict,
        "sub": "Out Baby Out%s &middot; %s &middot; %d players "
               "&middot; %d caught, %d brought back"
               % (" &middot; " + html.escape(title) if title else "",
                  clock(length),
                  sum(len(m) for m in teams.values()), tags, len(tree) - tags),
        "cards": cards,
        "stats": stats,
        "rows": "".join(lines),
        "foot": "Scored from the match log. Every line above was called on the "
                "day; nothing here is inferred.",
    }


EXAMPLE = """# Gachibowli, first game
LENGTH 20:00

RED   gokul, arjun, sai
BLUE  daniel, priya, rahul

02:14  gokul > priya
03:40  daniel + priya
07:02  priya > sai
09:15  gokul > rahul
11:48  arjun + sai
16:30  daniel > arjun
"""


def check():
    """One runnable check. Every case here is a way the score could move
    silently if the parser gave up instead of complaining."""
    length, teams, events = parse(EXAMPLE)
    assert length == 1200, length
    assert teams["RED"] == ["gokul", "arjun", "sai"], teams
    frozen, tree = play(length, teams, events)
    assert frozen == {"rahul", "arjun"}, frozen
    assert score(teams, frozen) == [("BLUE", 2, 3), ("RED", 2, 3)], \
        score(teams, frozen)
    assert len(tree) == 6

    # An amrit really does put someone back on the board.
    _, _, ev = parse("LENGTH 5:00\nA x\nB y\n01:00 x > y\n")
    assert play(300, {"A": ["x"], "B": ["y"]}, ev)[0] == {"y"}
    _, _, ev = parse("LENGTH 5:00\nA x, z\nB y\n01:00 x > y\n02:00 x + y\n")
    try:
        play(300, {"A": ["x", "z"], "B": ["y"]}, ev)
        assert False, "revived an enemy"
    except Bad:
        pass

    def refuses(log, because):
        try:
            length, teams, events = parse(log)
            play(length, teams, events)
        except Bad:
            return
        assert False, "accepted " + because

    refuses("A x\nB y\n01:00 x > y\n", "no LENGTH")
    refuses("LENGTH 5:00\nA x\n01:00 x > y\n", "one team")
    refuses("LENGTH 5:00\nA x\nB y\n01:00 x > ghost\n", "an unknown player")
    refuses("LENGTH 5:00\nA x, z\nB y\n01:00 x > z\n", "tagging a teammate")
    refuses("LENGTH 5:00\nA x\nB y\n01:00 x > y\n02:00 x > y\n",
            "freezing someone twice")
    refuses("LENGTH 5:00\nA x\nB y, w\n01:00 x > y\n02:00 y > x\n",
            "a frozen player acting")
    refuses("LENGTH 5:00\nA x\nB y\n02:00 x > y\n01:00 y + y\n",
            "events out of order")
    refuses("LENGTH 5:00\nA x\nB y\n09:00 x > y\n", "a tag after full time")
    refuses("LENGTH 5:00\nA x\nB x\n", "the same player on both teams")
    refuses("LENGTH 5:00\nA x\nB y\nsomething else\n", "a line it cannot read")
    refuses("LENGTH 5:00\nA x\nB y\n01:00 x > x\n", "acting on yourself")

    print("  all checks pass")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("log", nargs="?")
    ap.add_argument("--html", action="store_true", help="also write a page")
    ap.add_argument("--example", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        return check()

    if args.example:
        if os.path.exists("match.txt"):
            print("  match.txt already exists - not overwriting it.",
                  file=sys.stderr)
            return 2
        with io.open("match.txt", "w", encoding="utf-8", newline="\n") as fh:
            fh.write(EXAMPLE)
        print("  wrote match.txt - edit it, then: py -3 outbabyout.py match.txt")
        return 0

    if not args.log:
        ap.print_help()
        return 2
    if not os.path.isfile(args.log):
        print("  no file at %s" % args.log, file=sys.stderr)
        return 2

    with io.open(args.log, encoding="utf-8-sig", errors="replace") as fh:
        raw = fh.read()

    try:
        length, teams, events = parse(raw)
        frozen, tree = play(length, teams, events)
    except Bad as exc:
        # Not a scoreboard. A log this tool could not read must never come out
        # looking like a match that simply had few tags in it.
        print("\n  BLOCKED: %s" % exc, file=sys.stderr)
        print("  Nothing was scored, so nothing here is the result.\n",
              file=sys.stderr)
        return 2

    print(report(length, teams, frozen, tree))

    if args.html:
        title = label_of(raw)
        out = os.path.splitext(args.log)[0] + ".html"
        with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(page(title, length, teams, frozen, tree))
        print("  wrote %s\n" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
