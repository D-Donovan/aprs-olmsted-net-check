"""aprs-net-check -- who's around for the weekly net?

Checks a roster of amateur callsigns against aprs.fi and lists which members
were heard recently (default: last 2 hours) AND are within a radius (default
15 miles) of the 146.820 repeater -- a quick "who's on / nearby" aid for the
weekly meeting.

It uses the official aprs.fi API, which looks up the callsigns you name and
returns each one's last-known position and last-heard time from aprs.fi's
history database. (The API has no "everyone in an area" search, which is why a
roster is required -- it can only report on callsigns you list.)

Stdlib only (urllib + json); no pip installs.

Setup:
  1. Free aprs.fi account -> Account settings -> copy your API key.
  2. Provide it via  --apikey KEY,  env APRSFI_API_KEY,  or a file apikey.txt
     next to this script.
  3. Put your members in roster.txt (one callsign per line; see the sample).

Run:
  py -3.14 aprs_net_check.py                       # roster.txt, last 2 h, 15 mi
  py -3.14 aprs_net_check.py --hours 3 --radius 20
  py -3.14 aprs_net_check.py --all                 # also show absent members

Data courtesy of aprs.fi (https://aprs.fi/).
"""
import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- Configuration (override on the CLI) ---------------------------------
# 146.820 repeater: N44 01.270' W92 32.500'  ->  decimal degrees.
CENTER_LAT = 44.02117
CENTER_LON = -92.54167
RADIUS_MILES = 15.0
WINDOW_HOURS = 2.0
ROSTER_DEFAULT = os.path.join(HERE, "roster.txt")

API_URL = "https://api.aprs.fi/api/get"
API_BATCH = 20                       # aprs.fi allows up to 20 callsigns/query
USER_AGENT = "aprs-net-check/0.1 (+https://github.com/; APRS net helper)"
MILES_TO_KM = 1.609344


# ---- Helpers --------------------------------------------------------------
def haversine_miles(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dp / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return (r * 2 * math.asin(math.sqrt(a))) / MILES_TO_KM


def load_roster(path):
    """Parse roster.txt -> [(callsign, name)]. One entry per line:
        W0ABC-9            Jane Doe
        W0XYZ, John
    '#' starts a comment. Callsign is the first token; the rest is the name."""
    if not os.path.exists(path):
        sys.exit(f"roster not found: {path}\n"
                 f"Create it with one callsign per line (see roster.txt sample).")
    out, seen = [], set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.replace(",", " ").split(None, 1)
            call = parts[0].upper()
            name = parts[1].strip() if len(parts) > 1 else ""
            if call not in seen:
                seen.add(call)
                out.append((call, name))
    if not out:
        sys.exit(f"roster is empty: {path}")
    return out


def resolve_apikey(cli_key):
    if cli_key:
        return cli_key.strip()
    env = os.environ.get("APRSFI_API_KEY")
    if env:
        return env.strip()
    keyfile = os.path.join(HERE, "apikey.txt")
    if os.path.exists(keyfile):
        with open(keyfile, encoding="utf-8") as f:
            k = f.read().strip()
        if k:
            return k
    sys.exit("no aprs.fi API key. Provide --apikey KEY, set APRSFI_API_KEY, "
             "or put it in apikey.txt next to this script.\n"
             "Get a free key at aprs.fi -> Account settings -> API key.")


def aprsfi_locations(calls, apikey):
    """Query aprs.fi for up to API_BATCH calls at once; return {CALL: entry}
    merged across batches. Raises RuntimeError on an API-level failure."""
    result = {}
    for i in range(0, len(calls), API_BATCH):
        batch = calls[i:i + API_BATCH]
        params = urllib.parse.urlencode(
            {"name": ",".join(batch), "what": "loc",
             "apikey": apikey, "format": "json"})
        req = urllib.request.Request(f"{API_URL}?{params}",
                                     headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        if str(data.get("result")) != "ok":
            raise RuntimeError(data.get("description")
                               or f"aprs.fi returned: {data.get('result')}")
        for e in data.get("entries", []):
            name = (e.get("name") or "").upper()
            if name:
                result[name] = e            # last entry per call wins
        if i + API_BATCH < len(calls):
            time.sleep(3)                   # be polite between batches
    return result


# ---- Main -----------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="List roster members heard near the 146.820 repeater.")
    ap.add_argument("--roster", default=ROSTER_DEFAULT)
    ap.add_argument("--hours", type=float, default=WINDOW_HOURS,
                    help="heard-within window in hours (default 2)")
    ap.add_argument("--radius", type=float, default=RADIUS_MILES,
                    help="miles from the repeater (default 15)")
    ap.add_argument("--lat", type=float, default=CENTER_LAT)
    ap.add_argument("--lon", type=float, default=CENTER_LON)
    ap.add_argument("--apikey", default=None)
    ap.add_argument("--all", dest="show_all", action="store_true",
                    help="also list roster members who are absent, with reason")
    a = ap.parse_args()

    roster = load_roster(a.roster)
    apikey = resolve_apikey(a.apikey)
    calls = [c for c, _ in roster]
    names = dict(roster)

    try:
        found = aprsfi_locations(calls, apikey)
    except (urllib.error.URLError, RuntimeError, ValueError) as e:
        sys.exit(f"aprs.fi query failed: {e}")

    now = time.time()
    cutoff = a.hours * 3600
    present, absent = [], []
    for call in calls:
        e = found.get(call)
        name = names.get(call, "")
        if not e or "lasttime" not in e or "lat" not in e or "lng" not in e:
            absent.append((call, name, "no APRS data"))
            continue
        try:
            last = float(e["lasttime"])
            lat, lon = float(e["lat"]), float(e["lng"])
        except (TypeError, ValueError):
            absent.append((call, name, "unparseable position"))
            continue
        age = now - last
        dist = haversine_miles(a.lat, a.lon, lat, lon)
        if age <= cutoff and dist <= a.radius:
            present.append((call, name, age, dist))
        else:
            why = []
            if age > cutoff:
                why.append(f"last heard {_fmt_age(age)}")
            if dist > a.radius:
                why.append(f"{dist:.1f} mi out")
            absent.append((call, name, ", ".join(why)))

    present.sort(key=lambda r: r[2])        # most recently heard first
    print(f"Roster members heard within {a.radius:g} mi of the 146.820 "
          f"repeater in the last {a.hours:g} h:\n")
    print(f"  {'CALLSIGN':<11} {'LAST':>6}  {'DIST':>7}  NAME")
    for call, name, age, dist in present:
        print(f"  {call:<11} {_fmt_age(age):>6}  {dist:5.1f} mi  {name}")
    if not present:
        print("  (none)")
    print(f"\n{len(present)} of {len(roster)} roster members present.")
    if a.show_all and absent:
        print("\nabsent / not nearby:")
        for call, name, why in absent:
            print(f"  {call:<11} {why}" + (f"  ({name})" if name else ""))
    print("\nData: aprs.fi")


def _fmt_age(seconds):
    m = int(seconds // 60)
    if m < 60:
        return f"{m}m"
    h = m // 60
    return f"{h}h{m % 60:02d}m" if h < 24 else f"{h // 24}d"


if __name__ == "__main__":
    main()
