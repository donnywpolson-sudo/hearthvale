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
$AuditPath = ".codex\AUDIT.md"

if (-not (Test-Path $MetaAuditPath)) {
    throw "Missing $MetaAuditPath"
}

if (-not (Test-Path $AuditPath)) {
    throw "Missing $AuditPath"
}

$dirty = git status --porcelain
if ($dirty) {
    Write-Host "Repo is not clean. Stop and review git status first:" -ForegroundColor Red
    git status --short
    exit 1
}

$prompt = @"
Run one audit cycle.

Step 1:
Use $MetaAuditPath to inspect the current repo and update $AuditPath.
$AuditPath should become the best reusable project-specific audit prompt for this repo.

Step 2:
Using the updated $AuditPath, audit the repo and create one new timestamped audit report.
The audit report should identify what to improve.
Do not fix code during the audit step.

Step 3:
Read the new audit report and fix only the next smallest safe actionable batch.
Do not fix everything.
Do not do unrelated refactors.
Do not delete user work.
Do not commit.

Rules:
- Read files directly by path. Do not ask me to paste reports or logs.
- Keep changes minimal.
- Prefer targeted tests only.
- If full pytest is needed, ask me to run it instead of running it yourself.
- Update or create CODEX_HANDOFF.md with:
  - audit report path
  - files changed
  - issue fixed
  - tests/checks run
  - remaining findings
  - next recommended step

Expected allowed changes:
- $AuditPath
- one timestamped audit report
- CODEX_HANDOFF.md
- only source/test files needed for the single small remediation batch

Return only Changed, Notes/blockers, Next, Metrics.
"@

$prompt | codex exec --cd "$RepoRoot" --sandbox workspace-write -

Write-Host ""
Write-Host "Running local verification..." -ForegroundColor Cyan

$env:PYTHONDONTWRITEBYTECODE = "1"

python -B -m game.tools.validate_data
python -B -m pytest -p no:cacheprovider

Write-Host ""
Write-Host "Final git status:" -ForegroundColor Cyan
git status --short
