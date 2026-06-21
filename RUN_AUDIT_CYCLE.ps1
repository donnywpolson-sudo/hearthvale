$ErrorActionPreference = "Stop"

$RepoRoot = "C:\Users\donny\Desktop\hearthvale"
Set-Location -LiteralPath $RepoRoot

$ExpectedRepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$ActualRepoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) {
    throw "Failed to resolve git repo root from $RepoRoot"
}
$ActualRepoRoot = (Resolve-Path -LiteralPath $ActualRepoRoot).Path
if ($ActualRepoRoot -ne $ExpectedRepoRoot) {
    throw "Wrong repo root. Expected $ExpectedRepoRoot but got $ActualRepoRoot"
}

$MetaAuditPath = ".codex\META_AUDIT.md"
$CanonicalAuditPath = ".codex\AUDIT.md"
$AuditOutputDir = "reports\audit"
$CurrentAuditPath = Join-Path $AuditOutputDir "AUDIT_CURRENT.md"
$LatestReportPath = Join-Path $AuditOutputDir "AUDIT_REPORT_LATEST.md"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportPath = Join-Path $AuditOutputDir "AUDIT_REPORT_$Timestamp.md"

$dirty = @(git status --porcelain)
$blockingDirty = @()
foreach ($line in $dirty) {
    $path = $line.Substring(3).Trim()
    $allowed = (
        $path -eq "RUN_AUDIT_CYCLE.ps1" -or
        $path -eq "CODEX_HANDOFF.md" -or
        $path -like "reports/audit/*"
    )
    if (-not $allowed) {
        $blockingDirty += $line
    }
}
if ($blockingDirty) {
    Write-Host "Repo has non-audit changes. Stop and review git status first:" -ForegroundColor Red
    $blockingDirty | ForEach-Object { Write-Host $_ }
    exit 1
}
if ($dirty) {
    Write-Host "Continuing with existing audit-infrastructure changes:" -ForegroundColor Yellow
    git status --short
}

New-Item -ItemType Directory -Force -Path $AuditOutputDir | Out-Null

$MetaAuditStatus = if (Test-Path $MetaAuditPath) { "available at $MetaAuditPath" } else { "not available" }
$CanonicalAuditStatus = if (Test-Path $CanonicalAuditPath) { "available at $CanonicalAuditPath" } else { "not available" }

$prompt = @"
Run one audit cycle.

Step 1:
Use the meta-audit prompt if available ($MetaAuditStatus) and the canonical audit prompt if available ($CanonicalAuditStatus) to inspect the current repo and update $CurrentAuditPath.
$CanonicalAuditPath is an optional read-only canonical prompt location. Read it if available, but do not write to .codex and do not fail if .codex is read-only or unavailable.
$CurrentAuditPath should become the best reusable project-specific audit prompt for this repo.

Step 2:
Using the updated $CurrentAuditPath, audit the repo and create one new timestamped audit report at $ReportPath.
The audit report should identify what to improve.
Do not fix code during the audit step.

Step 3:
Read the new audit report and select only the next smallest safe actionable remediation batch.
Do not fix the selected batch yet.
Do not modify gameplay code, save migrations, protected-term policy, content data, visuals, audio, routines, or tests.
Do not delete user work.
Do not commit.

Rules:
- Read files directly by path. Do not ask me to paste reports or logs.
- Keep changes minimal.
- Prefer targeted tests only.
- If full pytest is needed, ask me to run it instead of running it yourself.
- Update or create CODEX_HANDOFF.md with:
  - audit report path
  - latest report pointer path
  - files changed
  - remediation batch selected
  - tests/checks run
  - remaining findings
  - next recommended step

Expected allowed changes:
- $CurrentAuditPath
- $ReportPath
- $LatestReportPath
- CODEX_HANDOFF.md
- no remediation/source/test/data/gameplay files

Return only Changed, Notes/blockers, Next, Metrics.
"@

$prompt | codex exec --cd "$RepoRoot" --sandbox workspace-write -

if (-not (Test-Path $ReportPath)) {
    throw "Audit report was not created at $ReportPath"
}

@"
# Latest Audit Report

Path: $ReportPath
Generated: $Timestamp
"@ | Set-Content -Path $LatestReportPath -Encoding UTF8

Write-Host ""
Write-Host "Running local verification..." -ForegroundColor Cyan

$env:PYTHONDONTWRITEBYTECODE = "1"

python -B -m game.tools.validate_data
python -B -m pytest -p no:cacheprovider

Write-Host ""
Write-Host "Final git status:" -ForegroundColor Cyan
git status --short
