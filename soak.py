"""A long unattended run, so the numbers stop being a snapshot.

Nothing moves during this. Both ceiling fans stay on the ceiling and the
laptop stays where it is. Any variation it records is noise, because there is
no signal - which is exactly the number the tag threshold has to survive.

    py -3 soak.py            about 10 minutes, writes soak.json
"""

import asyncio
import io
import json
import statistics
import sys
import time

sys.path.insert(0, ".")
import ruler

BEACONS = {
    "fan A": "08:92:72:2e:76:de",
    "fan B": "e8:f6:0a:40:1d:76",
}
MINUTES = 10
OUT = "soak.json"


async def go():
    seen = {name: [] for name in BEACONS}
    misses = {name: 0 for name in BEACONS}
    blocked = ""
    started = time.time()
    rounds = 0

    while time.time() - started < MINUTES * 60:
        try:
            rows = await ruler.scan(4)
        except ruler.Blocked as exc:
            # The radio stopping mid-run must not look like a quiet room for
            # the rest of the soak. Stop and say so.
            blocked = str(exc)
            break
        rounds += 1
        loud = {r[0].lower(): r[2] for r in rows}
        for name, address in BEACONS.items():
            if address in loud:
                seen[name].append(loud[address])
            else:
                misses[name] += 1

    report = {"rounds": rounds, "minutes": round((time.time() - started) / 60, 1),
              "blocked": blocked, "beacons": {}}
    for name, values in seen.items():
        if len(values) < 3:
            report["beacons"][name] = {"n": len(values), "note": "too few to judge",
                                       "missed_rounds": misses[name]}
            continue
        report["beacons"][name] = {
            "n": len(values),
            "median": statistics.median(values),
            "min": min(values), "max": max(values),
            "spread": max(values) - min(values),
            "stdev": round(statistics.stdev(values), 1),
            "stderr": round(statistics.stdev(values) / len(values) ** 0.5, 2),
            "missed_rounds": misses[name],
        }

    names = [n for n in seen if len(seen[n]) >= 3]
    if len(names) == 2:
        a, b = seen[names[0]], seen[names[1]]
        report["overlap"] = not (min(a) > max(b) or min(b) > max(a))
        report["median_gap"] = abs(statistics.median(a) - statistics.median(b))

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps(report, indent=1))
    return 2 if blocked else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(go()))
