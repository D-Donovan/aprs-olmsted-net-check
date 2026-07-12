# aprs-net-check

A small command-line helper for a weekly amateur-radio net: given a **roster**
of member callsigns, it reports which members were **heard recently** (default:
the last 2 hours) **and are within a radius** (default: 15 miles) of the
**146.820 MHz repeater** — a quick "who's on / nearby" list for the meeting.

It uses the official [aprs.fi](https://aprs.fi/) API. Data courtesy of aprs.fi.

## Why a roster?

The aprs.fi API looks up **specific callsigns you name** and returns each one's
last-known position and last-heard time from aprs.fi's history database. It does
**not** offer an "everyone within X miles" search, so the tool can only report
on callsigns you provide. For a club net with a known membership, that's exactly
what you want. (Live area *discovery* of unknown stations is possible only by
running your own APRS-IS collector — out of scope here.)

## Requirements

- Python 3.9+ (standard library only — no `pip install` needed).
- A free aprs.fi account and API key: sign in at aprs.fi → **Account settings** →
  copy your **API key**.

## Setup

1. Copy the sample roster and edit it with your members:
   ```
   copy roster.sample.txt roster.txt      # Windows
   # cp roster.sample.txt roster.txt      # macOS/Linux
   ```
   One callsign per line; text after the callsign is the name (optional).
   Use the **callsign-SSID** the member transmits APRS on (e.g. `W0ABC-9`).

2. Provide your API key one of these ways:
   - `--apikey YOURKEY` on the command line, or
   - environment variable `APRSFI_API_KEY`, or
   - a file `apikey.txt` next to the script (git-ignored).

## Usage

```
python aprs_net_check.py                     # roster.txt, last 2 h, 15 mi
python aprs_net_check.py --hours 3 --radius 20
python aprs_net_check.py --all               # also list absent members + reason
```

(On Windows you may need `py -3.14` instead of `python`.)

Example output:

```
Roster members heard within 15 mi of the 146.820 repeater in the last 2 h:

  CALLSIGN      LAST     DIST  NAME
  W0ABC-9        4m      2.1 mi  Jane Doe
  KC0XYZ        38m     11.4 mi  John Smith

2 of 12 roster members present.

Data: aprs.fi
```

### Options

| Option | Default | Meaning |
|---|---|---|
| `--roster PATH` | `roster.txt` | roster file |
| `--hours N` | `2` | "heard within" window |
| `--radius MI` | `15` | miles from the repeater |
| `--lat` / `--lon` | 44.02117 / -92.54167 | center (146.820 repeater) |
| `--apikey KEY` | — | aprs.fi API key (else env / file) |
| `--all` | off | also show absent members and why |

## Roster & auto-sync

The report reads `net-roster.txt` (one callsign per line; text after it is the
name). You can maintain it by hand, or import it from the club's membership
list:

```
python import_roster.py --paid-thru 2026 --wildcard   # -> net-roster.txt
```

`import_roster.py` pulls the RARC membership Google Sheet (published to the web,
so no login) and writes the active members. The **GitHub Action re-imports it on
every run** with the current year, so the published page always reflects the
club's current roster — no manual upkeep.

**Wildcards / SSIDs:** a trailing `*` (e.g. `W0TMP*`) matches the member on any
of their stations. The aprs.fi API has no wildcard search, so `*` is expanded to
the bare call plus a set of SSIDs — default `0,5,7,9,10` (home, phone, HT,
mobile, iGate). Change it with `--ssids`, e.g. `--ssids 0,7,9`. A member heard on
any of those counts once; the report shows the most-recently-heard SSID.

## Privacy / notes

- `roster.txt` and `apikey.txt` are **git-ignored** so your member list and key
  aren't committed. Only `roster.sample.txt` ships with the repo.
- `lasttime` from aprs.fi is the last time that station reported its current
  position; a station heard but not beaconing a position may not appear.
- Not affiliated with aprs.fi or the Rochester Amateur Radio Club. Per aprs.fi's
  terms, this tool is free to use and credits aprs.fi as the data source.

## License

MIT — see [LICENSE](LICENSE).
