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
$NextPromptFileName = "NEXT_REMEDIATION_PROMPT.md"
$NextPromptPath = Join-Path $RepoRoot $NextPromptFileName
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportPath = Join-Path $AuditOutputDir "AUDIT_REPORT_$Timestamp.md"

$dirty = @(git status --porcelain)
$blockingDirty = @()
foreach ($line in $dirty) {
    $path = $line.Substring(3).Trim()
    $allowed = (
        $path -eq "RUN_AUDIT_CYCLE.ps1" -or
        $path -eq "CODEX_HANDOFF.md" -or
        $path -eq "README.md" -or
        $path -eq "GRAPHICS_ANIMATION_NOTE.md" -or
        $path -eq "NEXT_REMEDIATION_PROMPT.md" -or
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

function Invoke-CodexPrompt {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PromptText
    )

    $PromptText | codex exec --cd "$RepoRoot" --sandbox workspace-write -
    if ($LASTEXITCODE -ne 0) {
        throw "Codex run failed."
    }
}

$MetaPrompt = @"
Run the meta-audit pass only.

Use the meta-audit prompt if available ($MetaAuditStatus) and the canonical audit prompt if available ($CanonicalAuditStatus) to inspect the current repo and update $CurrentAuditPath.
$CanonicalAuditPath is a read-only canonical prompt location. Read it if available, but do not write to .codex and do not fail if .codex is read-only or unavailable.
$CurrentAuditPath should become the best reusable project-specific audit prompt for this repo.
Do not create $ReportPath yet.
Do not fix code.
Do not commit.

Return only Changed, Notes/blockers, Selected batch, Next, Metrics.
"@

Invoke-CodexPrompt -PromptText $MetaPrompt

if (-not (Test-Path $CurrentAuditPath)) {
    throw "Audit prompt was not created at $CurrentAuditPath"
}

# Run the updated audit prompt file directly so the second Codex pass uses the repo prompt output.
$AuditRunIntro = @"
Run the audit cycle now.
The user explicitly asked for a timestamped audit report in this run.
Create exactly one new timestamped audit report at $ReportPath and no other files.
After the report is written, the outer script will read it and generate the remediation prompt.
Do not fix code.
Do not commit.
"@

Invoke-CodexPrompt -PromptText ($AuditRunIntro + "`n`n" + (Get-Content -Raw -LiteralPath $CurrentAuditPath))

if (-not (Test-Path $ReportPath)) {
    throw "Audit report was not created at $ReportPath"
}

$ReportText = Get-Content -Raw -LiteralPath $ReportPath
$SelectedBatchSectionMatch = [regex]::Match(
    $ReportText,
    '(?ms)^# Selected Remediation Batch\r?\n(?<body>.*?)(?:\r?\n# |\z)'
)
$RecommendedNextWorkSectionMatch = [regex]::Match(
    $ReportText,
    '(?ms)^# Recommended Next Work\r?\n(?<body>.*?)(?:\r?\n# |\z)'
)
$NextPromptSectionMatch = [regex]::Match(
    $ReportText,
    '(?ms)^# Next Codex Prompt\r?\n(?<body>.*)\s*$'
)

$SelectedBatch = ""
$SelectedBatchSeverity = ""
if ($SelectedBatchSectionMatch.Success) {
    $SelectedBatchSection = $SelectedBatchSectionMatch.Groups["body"].Value.Trim()
    $SelectedBatchMatch = [regex]::Match($SelectedBatchSection, '(?m)^\* Selected batch:\s*(.+)$')
    $SelectedBatchSeverityMatch = [regex]::Match($SelectedBatchSection, '(?m)^\* Selected batch severity:\s*(.+)$')
    $SelectedBatch = $SelectedBatchMatch.Groups[1].Value.Trim()
    $SelectedBatchSeverity = $SelectedBatchSeverityMatch.Groups[1].Value.Trim()
}

$NextPromptBody = if ($NextPromptSectionMatch.Success) {
    $NextPromptSectionMatch.Groups["body"].Value.Trim()
} elseif ($SelectedBatchSectionMatch.Success) {
    @"
Selected remediation batch:
$SelectedBatchSection

The report did not include a ready-to-paste next prompt section.
Use the selected remediation batch above to craft a separate Codex implementation run.
"@.Trim()
} else {
    @"
The report did not include a selected remediation batch or next prompt section.
Review $ReportPath and craft a separate Codex implementation run from the report findings.
"@.Trim()
}

@"
# Latest Audit Report

Path: $ReportPath
Generated: $Timestamp
Audit-only: yes
Remediation applied: no
Selected batch prompt path: $NextPromptFileName
Next action: paste the generated prompt into a separate approved remediation goal
"@ | Set-Content -Path $LatestReportPath -Encoding UTF8

$NextPrompt = @"
# Next Remediation Prompt

Source report: $ReportPath
Latest report pointer: $LatestReportPath
Selected batch prompt path: $NextPromptFileName
Selected batch: $SelectedBatch
Severity: $SelectedBatchSeverity

$NextPromptBody
"@

Set-Content -LiteralPath $NextPromptPath -Value $NextPrompt -Encoding UTF8

Write-Host ""
Write-Host "Recommended next work:" -ForegroundColor Cyan
if ($RecommendedNextWorkSectionMatch.Success) {
    Write-Host $RecommendedNextWorkSectionMatch.Groups["body"].Value.Trim()
} else {
    Write-Host "No recommended next work section found in $ReportPath."
}

Write-Host ""
Write-Host "Paste-ready prompt written to $NextPromptFileName" -ForegroundColor Cyan

Write-Host ""
Write-Host "Final git status:" -ForegroundColor Cyan
git status --short
