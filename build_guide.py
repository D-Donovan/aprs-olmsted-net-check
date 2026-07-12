"""Generate the member-facing PDF guide for aprs-olmsted-net-check.

Writes a styled HTML document and renders it to
docs/APRS-Olmsted-Net-Check-Guide.pdf using headless Microsoft Edge (or Chrome).
No pip packages required -- it drives a browser already on the machine.

    py -3.14 build_guide.py
"""
import datetime
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "docs")
PDF = os.path.join(OUT_DIR, "APRS-Olmsted-Net-Check-Guide.pdf")
HTML = os.path.join(OUT_DIR, "_guide.html")

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

PAGE_URL = "https://d-donovan.github.io/aprs-olmsted-net-check/"
REPO_URL = "https://github.com/D-Donovan/aprs-olmsted-net-check"

DOC = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>APRS Net Check Guide</title>
<style>
  @page {{ size: letter; margin: 0.8in; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: "Segoe UI", system-ui, Arial, sans-serif; color: #1a1a1a;
         font-size: 10.5pt; line-height: 1.45; margin: 0; }}
  h1 {{ font-size: 22pt; margin: 0 0 2pt; color: #0b3d6b; }}
  h2 {{ font-size: 13pt; margin: 20pt 0 5pt; color: #0b3d6b;
       border-bottom: 2px solid #d5e2ef; padding-bottom: 3pt; }}
  h3 {{ font-size: 11pt; margin: 12pt 0 3pt; }}
  .lead {{ color: #444; font-size: 11pt; margin: 0 0 4pt; }}
  .meta {{ color: #777; font-size: 9pt; margin: 0 0 6pt; }}
  code {{ font-family: Consolas, monospace; background: #f0f3f7;
         padding: 1px 4px; border-radius: 3px; font-size: 9.5pt; }}
  a {{ color: #0b5cad; text-decoration: none; }}
  ul {{ margin: 4pt 0 4pt 0; padding-left: 18pt; }}
  li {{ margin: 2pt 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 6pt 0; }}
  th, td {{ text-align: left; vertical-align: top; padding: 5pt 7pt;
           border: 1px solid #cdd8e4; font-size: 9.8pt; }}
  th {{ background: #eaf1f8; color: #0b3d6b; }}
  .box {{ background: #f7f9fc; border: 1px solid #d5e2ef; border-radius: 6px;
         padding: 8pt 12pt; margin: 8pt 0; }}
  .callout {{ background: #fff8e6; border: 1px solid #f0dca0; }}
  .foot {{ margin-top: 18pt; border-top: 1px solid #ccc; padding-top: 6pt;
          color: #777; font-size: 8.5pt; }}
  .avoid-break {{ break-inside: avoid; }}
</style></head><body>

<h1>Olmsted County APRS Net &mdash; Check-in Board</h1>
<p class="lead">A live web page showing which club members have been heard on
APRS near the 146.820 repeater around net time.</p>
<p class="meta">Rochester Amateur Radio Club &middot; Net: Sundays 9:00&nbsp;PM
Central &middot; Guide version 1.0 ({datetime.date.today():%B %Y})</p>

<h2>What it is</h2>
<p>Before and during the weekly net, this tool checks the club roster against
<a href="https://aprs.fi/">aprs.fi</a> and lists the members whose APRS stations
were <strong>heard in the last 2 hours</strong> and are <strong>within 15 miles
of the 146.820 repeater</strong>. It's a quick "who's on / nearby tonight"
board &mdash; a helper for check-ins, not an official log.</p>

<h2>Where to find it</h2>
<div class="box"><strong>Web page:</strong>
  <a href="{PAGE_URL}">{PAGE_URL}</a><br>
  Bookmark it on your phone or computer. The page refreshes itself every 60
  seconds, so you can leave it open during the net.</div>

<h2>When it updates</h2>
<ul>
  <li>Automatically on <strong>Sundays at 8:45, 9:00, and 9:15&nbsp;PM
      Central</strong> (it adjusts for daylight-saving time on its own).</li>
  <li>The page shows the time it was generated. Between updates it holds the
      last result.</li>
</ul>

<h2>How to read the page</h2>
<ul>
  <li><strong>Present</strong> table &mdash; each member heard in range, with
      how long ago they were last heard, their distance from the repeater, and
      their name.</li>
  <li><strong>&ldquo;N of M present&rdquo;</strong> &mdash; how many of the
      roster were heard in range.</li>
  <li><strong>&ldquo;not present / not nearby&rdquo;</strong> &mdash; expandable
      list of everyone else, with the reason (heard too long ago, or too far).</li>
</ul>

<h2>How to make sure you show up</h2>
<div class="box callout avoid-break">
<ol>
  <li>Be <strong>transmitting APRS</strong> (a position beacon) from a station
      within ~15 miles of the repeater.</li>
  <li>Have been <strong>heard within the last 2 hours</strong> of the update.</li>
  <li>Your callsign must be on the <strong>RARC membership roster</strong>
      (current/paid members; imported automatically &mdash; see below).</li>
  <li>Transmit on one of the recognized <strong>SSIDs</strong>: none (home),
      <code>-5</code> (phone apps), <code>-7</code> (HT), <code>-9</code>
      (mobile), or <code>-10</code> (iGate). Example: a mobile rig usually
      beacons as <code>YOURCALL-9</code>.</li>
</ol>
</div>

<h3>&ldquo;I was on but not listed&rdquo; &mdash; common reasons</h3>
<ul>
  <li>Last APRS beacon was more than 2 hours ago (check your tracker is
      beaconing).</li>
  <li>You were outside the 15-mile radius when last heard.</li>
  <li>You transmit on an SSID that isn't in the list above.</li>
  <li>Your callsign isn't on the current membership sheet, or is spelled/keyed
      differently there.</li>
</ul>

<h2>Where the member list comes from</h2>
<p>The roster is imported automatically from the club's own
<strong>membership Google Sheet</strong> (the one published on the RARC
website). Only <strong>current (paid) members</strong> are included, and it
re-imports on every update, so it stays in sync as membership changes &mdash;
no separate list to maintain.</p>

<h2>Privacy &amp; data</h2>
<ul>
  <li>Uses only <strong>public APRS data</strong> (the same you can see on
      aprs.fi) and <strong>public callsign/name</strong> info from the club's
      published membership sheet.</li>
  <li>No location history is stored; each update is a fresh snapshot.</li>
  <li>Data is courtesy of <a href="https://aprs.fi/">aprs.fi</a>.</li>
</ul>

<h2>Technologies used</h2>
<table>
  <tr><th>Technology</th><th>Role in this project</th></tr>
  <tr><td><strong>APRS</strong> (Automatic Packet Reporting System)</td>
      <td>The amateur-radio network where stations beacon position &amp; status
          over RF. The underlying data source.</td></tr>
  <tr><td><strong>APRS-IS</strong></td>
      <td>The internet backbone that aggregates APRS traffic worldwide; what
          aprs.fi ingests.</td></tr>
  <tr><td><strong>aprs.fi API</strong></td>
      <td>Public web API queried for each member's last-heard time and last
          known position. Access via a free API key.</td></tr>
  <tr><td><strong>Python 3</strong> (standard library only)</td>
      <td>The two programs &mdash; <code>aprs_net_check.py</code> (builds the
          report) and <code>import_roster.py</code> (pulls the roster). No
          third-party packages.</td></tr>
  <tr><td><strong>Google Sheets</strong> (published to the web)</td>
      <td>The RARC membership roster, read as CSV to build the current member
          list.</td></tr>
  <tr><td><strong>GitHub</strong></td>
      <td>Source repository. <strong>GitHub Actions</strong> runs the scheduled
          builds; <strong>GitHub Pages</strong> hosts the web page; an
          <strong>encrypted Actions Secret</strong> holds the API key.</td></tr>
  <tr><td><strong>HTML &amp; CSS</strong></td>
      <td>The report web page (self-contained, auto-refreshing).</td></tr>
  <tr><td><strong>cron</strong> (UTC)</td>
      <td>Schedule expressions that trigger the Sunday-evening builds.</td></tr>
  <tr><td><strong>Microsoft Edge</strong> (headless)</td>
      <td>Renders this PDF guide from HTML (build step only).</td></tr>
</table>

<h2>For maintainers</h2>
<ul>
  <li><strong>Source &amp; docs:</strong> <a href="{REPO_URL}">{REPO_URL}</a>
      (see <code>README.md</code>).</li>
  <li><strong>Settings</strong> (repeater location, radius, time window, SSIDs,
      roster source) live in <code>config.json</code> &mdash; edit and commit.</li>
  <li><strong>Refresh on demand:</strong> repo &rarr; Actions &rarr;
      &ldquo;Net report&rdquo; &rarr; Run workflow. Or run
      <code>py aprs_net_check.py</code> locally.</li>
  <li><strong>Schedule</strong> is in <code>.github/workflows/report.yml</code>
      (GitHub requires cron there, not in config).</li>
  <li><strong>API quota:</strong> the free aprs.fi key is rate-limited; the tool
      backs off and the schedule is kept light. Request a higher quota from
      aprs.fi for heavier use.</li>
</ul>

<p class="foot">Prepared for the Rochester Amateur Radio Club. Not affiliated
with aprs.fi. This tool is free to use; data courtesy of aprs.fi.
&middot; {PAGE_URL}</p>

</body></html>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(DOC)
    browser = next((b for b in BROWSERS if os.path.exists(b)), None)
    if not browser:
        sys.exit("no Edge/Chrome found to render the PDF; install one or edit "
                 "BROWSERS. The HTML was written to " + HTML)
    file_url = "file:///" + HTML.replace("\\", "/")
    cmd = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={PDF}", file_url]
    subprocess.run(cmd, check=True, timeout=120,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(PDF):
        sys.exit("browser ran but no PDF was produced.")
    print(f"wrote {PDF} ({os.path.getsize(PDF) // 1024} KB)")


if __name__ == "__main__":
    main()
