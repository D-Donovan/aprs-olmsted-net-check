# Fire the aprs-olmsted-net-check GitHub workflow on demand.
#
# Run by Windows Task Scheduler at the net times on Sundays. It POSTs a
# workflow_dispatch to the GitHub API (explicit ref=main), which builds
# immediately and bypasses the workflow's time-gate -- so the page updates right
# at net time regardless of GitHub's flaky cron. Uses the existing gh login
# (Windows credential store); no token is stored in this file.
#
# Uses the raw API endpoint rather than `gh workflow run` (which resolves the
# ref itself and was observed returning transient HTTP 500s), and retries with
# backoff so a brief GitHub hiccup doesn't drop a net-night fire.
$Repo = 'D-Donovan/aprs-olmsted-net-check'
$Gh   = 'C:\Users\dad03\Desktop\claude_project\SkyRavenPy\.tools\bin\gh.exe'
if (-not (Test-Path $Gh)) { $Gh = 'gh' }        # fall back to gh on PATH
$Log  = Join-Path $PSScriptRoot 'trigger_net_report.log'
function Now { Get-Date -Format 'yyyy-MM-dd HH:mm:ss' }

$ok = $false
for ($i = 1; $i -le 4 -and -not $ok; $i++) {
    & $Gh api --method POST "repos/$Repo/actions/workflows/report.yml/dispatches" `
        -f ref=main *> $null
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    Start-Sleep -Seconds (10 * $i)              # 10s, 20s, 30s backoff
}
Add-Content -Path $Log -Value ("{0}  {1}" -f (Now),
    $(if ($ok) { 'dispatched report.yml OK' }
      else { 'ERROR: dispatch failed after 4 attempts' }))
if (-not $ok) { exit 1 }
