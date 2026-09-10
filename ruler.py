"""Can a phone tell 2 metres from 10? Measure it before building anything.

The whole game rests on one assumption: that a tag can fire when two people
are close and not when they are not. Bluetooth does not report distance. It
reports RSSI - how loud the radio sounds - and loudness through a body, a
pocket, or a wall is not distance. If the reading at 2m overlaps the reading
at 10m, the app cannot work as designed and it is better to know that today
than after writing it.

This measures that, with a laptop standing in for the second phone.

    py -3 ruler.py                        what is nearby, loudest first
    py -3 ruler.py --track AA:BB:...      follow one device, live
    py -3 ruler.py --sample AA:BB:... --at 2
                                          record readings at a marked distance
    py -3 ruler.py --verdict              can the distances be told apart

Needs `bleak`, which is a measuring tool, not a dependency of the game. The
match engine stays standard library only.

How to run it properly, because a sloppy version of this answers nothing:

  1. Put the phone in Bluetooth settings so it stays advertising, and leave
     the screen on.
  2. Mark the floor at 1, 2, 5 and 10 metres with tape.
  3. --sample at each mark, phone held in the hand, standing still.
  4. Then do 2m again with the phone in a trouser pocket and your body between
     it and the laptop. That is the reading that decides it - a tag in a real
     game happens with the phone in a pocket and people in the way.
"""

import argparse
import asyncio
import io
import json
import os
import statistics
import sys
import time

try:
    from bleak import BleakScanner
except ImportError:
    print("  BLOCKED: bleak is not installed.\n"
          "  py -3 -m pip install bleak", file=sys.stderr)
    raise SystemExit(2)

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

class Blocked(Exception):
    """The radio could not be used. Never the same thing as seeing nothing."""


READINGS = "rssi.json"
# Long enough that a slow advertiser is still seen, short enough to stand still.
SAMPLE_SECONDS = 20


def load():
    if not os.path.exists(READINGS):
        return {}
    try:
        with io.open(READINGS, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except Exception as exc:
        # A readings file that will not parse is not an empty experiment.
        # Returning {} here would silently throw away every measurement taken
        # so far and print a verdict from nothing.
        print("  BLOCKED: could not read %s: %s" % (READINGS, exc),
              file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict):
        print("  BLOCKED: %s is not an object" % READINGS, file=sys.stderr)
        raise SystemExit(2)
    return data


def save(data):
    tmp = READINGS + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
    os.replace(tmp, READINGS)


async def scan(seconds):
    """[(address, name, rssi)] seen in this window, loudest first."""
    found = {}

    def seen(device, advert):
        rssi = getattr(advert, "rssi", None)
        if rssi is None:
            return
        found.setdefault(device.address, []).append(rssi)
        found[device.address + "|name"] = device.name or advert.local_name or "?"

    scanner = BleakScanner(detection_callback=seen)
    try:
        await scanner.start()
        await asyncio.sleep(seconds)
        await scanner.stop()
    except Exception as exc:
        # A radio that never started is not a quiet room. Letting this reach
        # the caller as an empty list would print "nothing advertising - that
        # is a real empty", which is the exact lie this whole project keeps
        # finding in its own code.
        raise Blocked(str(exc))

    out = []
    for key, values in found.items():
        if key.endswith("|name"):
            continue
        out.append((key, found.get(key + "|name", "?"),
                    round(statistics.median(values)), len(values)))
    return sorted(out, key=lambda r: -r[2])


def show(rows):
    if not rows:
        # An empty scan is a result only if the radio actually ran. It did -
        # the scanner started and stopped without raising - so this is a real
        # "nothing was advertising", not a failure to look.
        print("\n  Nothing advertising. That is a real empty: the scan ran.")
        print("  Is the phone's Bluetooth screen open and the screen on?\n")
        return
    print("\n  %-22s %-26s %6s %6s" % ("ADDRESS", "NAME", "RSSI", "SEEN"))
    print("  " + "-" * 62)
    for address, name, rssi, count in rows[:15]:
        print("  %-22s %-26s %6d %6d" % (address, name[:26], rssi, count))
    print("\n  Louder (closer to 0) is nearer. Pick your phone and --track it.\n")


async def track(address):
    print("\n  Following %s. Walk. Ctrl-C to stop.\n" % address)
    try:
        while True:
            rows = await scan(3)
            hit = [r for r in rows if r[0].lower() == address.lower()]
            if not hit:
                print("  %s   ...gone" % time.strftime("%H:%M:%S"))
                continue
            rssi = hit[0][2]
            bar = "#" * max(0, min(40, rssi + 100))
            print("  %s  %4d dBm  %s" % (time.strftime("%H:%M:%S"), rssi, bar))
    except KeyboardInterrupt:
        print("\n  stopped\n")


async def sample(address, metres, note):
    print("\n  Hold still for %d seconds at %s m..." % (SAMPLE_SECONDS, metres))
    rows = []
    deadline = time.time() + SAMPLE_SECONDS
    while time.time() < deadline:
        found = await scan(3)
        hit = [r for r in found if r[0].lower() == address.lower()]
        if hit:
            rows.append(hit[0][2])
            print("    %4d dBm" % hit[0][2])

    if not rows:
        print("\n  BLOCKED: never saw %s in %d seconds." % (address,
                                                            SAMPLE_SECONDS))
        print("  Nothing recorded. An unseen device is not a weak reading -\n"
              "  saving it as one would drag the average and fake the verdict.\n",
              file=sys.stderr)
        return 2

    data = load()
    key = "%s m%s" % (metres, (" " + note) if note else "")
    data.setdefault(key, []).extend(rows)
    save(data)
    print("\n  %s: %d readings, median %d dBm (was %d total)\n"
          % (key, len(rows), round(statistics.median(rows)), len(data[key])))
    return 0


def verdict():
    """Do the distances actually separate, or do they overlap?"""
    data = load()
    if not data:
        print("\n  Nothing measured yet. Take samples first.\n", file=sys.stderr)
        return 2

    print("\n  %-18s %5s %8s %8s %8s" % ("AT", "N", "MEDIAN", "WORST", "BEST"))
    print("  " + "-" * 52)
    spans = {}
    for key in sorted(data, key=lambda k: (float(k.split()[0]), k)):
        values = data[key]
        if len(values) < 3:
            print("  %-18s %5d   too few to judge" % (key, len(values)))
            continue
        spans[key] = (min(values), max(values))
        print("  %-18s %5d %8d %8d %8d"
              % (key, len(values), round(statistics.median(values)),
                 min(values), max(values)))

    print()
    near = [k for k in spans if float(k.split()[0]) <= 2]
    far = [k for k in spans if float(k.split()[0]) >= 5]
    if not near or not far:
        print("  Need at least one reading at 2m or under AND one at 5m or"
              " over\n  before this can say anything.\n")
        return 2

    worst_near = min(spans[k][0] for k in near)   # quietest close reading
    best_far = max(spans[k][1] for k in far)      # loudest far reading

    if worst_near > best_far:
        print("  SEPARATED. The quietest close reading (%d) is still louder"
              % worst_near)
        print("  than the loudest far one (%d). A threshold between them"
              % best_far)
        print("  would call every tag right in these conditions.\n")
        print("  Now redo 2m with the phone in a pocket and a body in the way.")
        print("  If it still separates, the app is possible.\n")
        return 0

    print("  OVERLAP of %d dBm. The quietest close reading (%d) is weaker"
          % (worst_near - best_far if worst_near < best_far
             else 0, worst_near))
    print("  than the loudest far one (%d), so no single threshold can tell"
          % best_far)
    print("  them apart. Raw RSSI is not enough on its own.\n")
    print("  That is a real finding, not a failure. It means a tag needs")
    print("  something more than one reading - several in a row, both phones")
    print("  agreeing, or a confirm button. Better to know now.\n")
    return 1


def main():
    try:
        return run()
    except Blocked as exc:
        print("\n  BLOCKED: %s" % exc, file=sys.stderr)
        print("  The scan never ran, so nothing here says anything about"
              " distance.", file=sys.stderr)
        print("  Turn Bluetooth on in Windows Settings and try again.\n",
              file=sys.stderr)
        return 2


def run():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--track", metavar="ADDRESS")
    ap.add_argument("--sample", metavar="ADDRESS")
    ap.add_argument("--at", metavar="METRES", help="distance for --sample")
    ap.add_argument("--note", default="", help='e.g. "pocket"')
    ap.add_argument("--verdict", action="store_true")
    ap.add_argument("--seconds", type=int, default=8)
    args = ap.parse_args()

    if args.verdict:
        return verdict()
    if args.track:
        return asyncio.run(track(args.track)) or 0
    if args.sample:
        if not args.at:
            print("  --sample needs --at, e.g. --at 2", file=sys.stderr)
            return 2
        try:
            float(args.at)
        except ValueError:
            print("  --at wants a number of metres", file=sys.stderr)
            return 2
        return asyncio.run(sample(args.sample, args.at, args.note))

    show(asyncio.run(scan(args.seconds)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
