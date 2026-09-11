# Constraints not to rediscover

Things already tried on this machine that already failed. Each one cost real time once.
Read this before starting; add to it before finishing.

## This machine

**Bash heredocs eat backslashes.** A patch script fed through `py -3 - <<'PY'` has its
`\n` turned into a real newline before Python sees it, so any string literal containing
one becomes an unterminated string. This has broken a file **four separate times in one
day**, including twice after it was already written down.

> Use the Write or Edit tool for patch scripts. Never a heredoc.

**Use `py -3`, never `python`.** The Store build of Python is sandboxed and writes to a
shadow filesystem, so files it creates appear to vanish.

**PowerShell's `-Encoding utf8` writes a BOM.** Anything reading those files must open
them `utf-8-sig`, or the first key of a JSON object arrives with an invisible prefix and
`json.loads` fails on a file that looks perfect in an editor.

**Windows caps a command line at 32 KB.** A long prompt passed in argv fails as
"The filename or extension is too long", which does not sound like the actual problem.
Pass it on stdin.

## Bluetooth, measured 10 Sept 2026

**RSSI is not distance, and the noise is bigger than the signal.** With the laptop and a
ceiling-fan beacon both completely stationary, ten consecutive readings spanned
**24 dBm** (min -74, max -50, stdev 7.7).

Signal falls roughly 6 dBm per doubling of distance indoors. A 24 dBm spread with nothing
moving is therefore about four doublings of ambiguity — the noise alone covers something
like 1 m to 16 m.

> **A single RSSI reading cannot tell 2 m from 10 m.** Any tag rule built on one reading
> is already wrong. A tag needs several readings in a row, both devices agreeing, or a
> human confirming.

**Averaging helps, and by how much is known.** Twelve samples of one beacon tightened the
standard error of the median to about **1.1 dBm**, and two beacons at different distances
separated by 12 dBm at the median — while their **raw ranges still overlapped**. So the
median is usable and any individual reading is not.

**Then the ten-minute soak settled it. 145 rounds, nothing moving:**

| | fan A | fan B |
|---|---|---|
| median | −68 | −76 |
| spread | **35 dBm** (−78 to −43) | 18 dBm |
| stdev | 11.1 | 6.9 |
| stderr of median | 0.92 | 0.58 |

Ranges overlap. **The two beacons' medians differ by only 8 dBm while a single stationary
beacon swings 35.** The longer the window, the worse the spread got — 24 dBm over ten
readings, 35 over 145.

Working out what that costs: separating an 8 dBm gap against a stdev of 11.1 needs about
**31 samples**, arriving at the observed 14.4 per minute, so a confident call takes about
**two minutes**.

> **A tag has to fire in about two seconds. RSSI needs about two minutes. That is a 60x
> gap, and it is not closeable by tuning.**

**So the tag is not a radio measurement. It should be a scan.** A QR code on the target's
screen, or an NFC tap. That is instant, cannot be faked from across the street, needs no
background advertising, does not care that addresses rotate, works on every phone, and
costs no battery. It also matches the real game: you are standing right in front of the
person when you tag them.

Keep `ruler.py` and `soak.py`. They are the evidence for why the design is what it is.

**Phones do not appear in a plain scan.** A twenty-second scan of this room found two
ceiling fans advertising steadily and several devices with rotating addresses seen only a
few times each. Phones randomise their Bluetooth address for privacy and do not advertise
continuously in the background without an app doing it deliberately.

> This is the real obstacle to the app, and it is larger than the RSSI one. **Verify it
> properly before writing any app code**: it decides whether this is an app or an
> OS-level problem. It is why contact tracing needed Apple and Google rather than an
> ordinary app.

**`bleak` has no `__version__` attribute.** `import bleak; bleak.__version__` raises
`AttributeError` even on a perfectly good install. Do not read that as a failed install.

**A powered-off radio raises, it does not return nothing.** `bleak` raises
`BleakBluetoothNotAvailableError`. `ruler.py` deliberately converts that to `Blocked` and
exits 2. **Do not "fix" this by catching it and returning an empty list** — an unpowered
adapter would then print as a quiet room, which is the single bug this whole project
exists to avoid.

## Third-party services, 11 Sept 2026

**A service that needed no key when you chose it can start needing one.** The field map
was built on CARTO's dark basemap because it matched the palette. CARTO now requires an
API key and stamps **API KEY REQUIRED** across every tile served without one. It rendered
fine in the local check and was caught by Gokul opening it on his own phone.

> Before using any third-party URL, check whether it requires a key **today**, and write
> the answer here with the date.

Replaced with `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, which needs no key and
has none to expire. It is drawn light, so `.leaflet-tile-pane` carries a CSS filter
rather than paying for a dark basemap. Attribution is required and is present.

**Check the deployed URL, not the local file.** They are different origins with different
caches. The watermark got past a local check because those tiles were already cached; a
clean phone showed it immediately. Push, wait for the Pages build, then look.

**Nominatim** (the search box) needs no key either, asks for roughly one request a second,
and identifies callers by browser Referer, which a normal page supplies.

## Rules of this codebase

**A failed read is never a result.** Everywhere: an unreadable log is BLOCKED and exits 2,
never a scoreboard. An unseen device is not a weak reading and is not saved as one. A
zero must always be distinguishable from a failure to look.

**The engine has no dependencies.** `bleak` belongs to the radio side only. If the engine
ever imports it, the rules stop being provable on a machine without an adapter.

**No live location, ever.** Direction and distance only. Every app in this category died
on live position: Zenly shut down, Life360 was sued, Instagram Map drew 37 state attorneys
general. This is designed out, not configured off.

**No tag above walking pace.** There is no code path that writes a tag while moving. Not a
rule that can be relaxed — the field does not exist.
