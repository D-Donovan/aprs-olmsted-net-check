"""Import the RARC member roster into net-roster.txt.

The club's membership page (rarchams.org/wp/membership-2/) embeds a Google Sheet
that is *published to the web*, so its CSV export is publicly readable -- no
login or API key. This pulls that CSV and writes the roster in the format
aprs_net_check.py expects.

  py -3.14 import_roster.py                  # -> net-roster.txt (bare calls)
  py -3.14 import_roster.py --wildcard       # write CALL* (match any SSID)
  py -3.14 import_roster.py --paid-thru 2026 # only members paid thru >= 2026
  py -3.14 import_roster.py --out preview.txt

Note on --wildcard: each CALL* becomes 16 aprs.fi lookups (bare + -1..-15).
With ~99 members that's ~1600 lookups per report build -- fine occasionally,
but consider a lighter refresh schedule if you enable it for everyone.
"""
import argparse
import csv
import io
import re
import sys
import urllib.error
import urllib.request

# "Publish to web" CSV export of the sheet embedded on the membership page.
SHEET_CSV = ("https://docs.google.com/spreadsheets/d/e/"
             "2PACX-1vS6rTXV8oJdJut9OSWFtrbMqS5LO7ojncxmrgaLF27EqzgM_"
             "NSrEfTZmbiBn6NL9tSdCkUj5LFkElQe/pub"
             "?gid=1526286142&single=true&output=csv")
OUT_DEFAULT = "net-roster.txt"
USER_AGENT = "aprs-net-check import/0.1"
# Lenient US-style callsign check (1-2 letters, a digit, 1-4 letters).
CALL_RE = re.compile(r"^[A-Z]{1,2}[0-9][A-Z]{1,4}$")


def fetch_csv(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_members(text, paid_thru=None):
    """Yield (call, name) from the sheet CSV. Skips non-callsign rows and, if
    paid_thru is set, members whose 'Membership Paid Thru' year is older."""
    reader = csv.DictReader(io.StringIO(text))
    # Tolerate header label variations.
    def col(row, *names):
        for n in names:
            for k in row:
                if k and k.strip().lower() == n:
                    return (row[k] or "").strip()
        return ""
    for row in reader:
        call = col(row, "call", "callsign", "call sign").upper()
        if not CALL_RE.match(call):
            continue
        if paid_thru is not None:
            yr = col(row, "membership paid thru", "paid thru", "paid through")
            m = re.search(r"\d{4}", yr)
            if not m or int(m.group()) < paid_thru:
                continue
        first = col(row, "first name", "first")
        last = col(row, "last name", "last")
        yield call, (first + " " + last).strip()


def main():
    ap = argparse.ArgumentParser(description="Import RARC roster from the "
                                 "published Google Sheet into net-roster.txt.")
    ap.add_argument("--url", default=SHEET_CSV, help="sheet CSV export URL")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--wildcard", action="store_true",
                    help="append '*' to each call so any SSID matches "
                         "(≈16x more aprs.fi lookups)")
    ap.add_argument("--paid-thru", type=int, default=None, metavar="YEAR",
                    help="only members paid through this year or later")
    a = ap.parse_args()

    try:
        text = fetch_csv(a.url)
    except (urllib.error.URLError, OSError) as e:
        sys.exit(f"could not fetch the sheet: {e}")

    members = list(parse_members(text, a.paid_thru))
    if not members:
        sys.exit("no member callsigns parsed -- the sheet layout may have "
                 "changed; check the URL/columns.")
    seen, uniq = set(), []               # the sheet can contain duplicate rows
    for c, n in members:
        if c not in seen:
            seen.add(c)
            uniq.append((c, n))
    members = sorted(uniq)

    width = max(len(c) for c, _ in members) + (1 if a.wildcard else 0)
    lines = ["# Olmsted County net roster -- imported from the RARC membership",
             "# Google Sheet (rarchams.org). Regenerate with import_roster.py.",
             f"# {len(members)} members"
             + (f", paid thru >= {a.paid_thru}" if a.paid_thru else "")
             + (", wildcard SSIDs" if a.wildcard else "") + ".",
             ""]
    for call, name in members:
        tag = (call + "*") if a.wildcard else call
        lines.append(f"{tag:<{width + 1}} {name}".rstrip())
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {a.out}: {len(members)} members"
          + (" (wildcard)" if a.wildcard else ""))


if __name__ == "__main__":
    main()
