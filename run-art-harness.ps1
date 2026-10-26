# Unified harness entry. Exit codes are the harness contract (see HARNESS.md):
#   0 accepted only for controller-approved exact inputs
#   2 blocked / invalid inputs (gate error, missing key, bad signature)
#   3 valid run but not accepted (draft, failed checks, needs review)
#
# New (documented) form:
#   .\run-art-harness.ps1 -Command audit -Stage art_complete -Quality delivery\...\behavior_results.json
#   .\run-art-harness.ps1 -Command prepare -Stage scene_demo -Artifacts spec.json -Out art_review\submissions\current\manifest.json
#   .\run-art-harness.ps1 -Command verify -Manifest ... -Review ... -Attestation ... -Certificate ...
# Legacy passthrough still works:
#   .\run-art-harness.ps1 verify --manifest ... --review ...
param(
    [Parameter(Position = 0)]
    [ValidateSet("audit", "prepare", "verify", "attest", "certify")]
    [string]$Command,
    [string]$Stage,
    [string]$Artifacts,
    [string]$Manifest,
    [string]$Review,
    [string]$Attestation,
    [string]$Certificate,
    [string]$Out,
    [string]$Dependencies,
    [string]$CertificateId,
    [string]$ApprovalScope,
    [string]$Quality,
    [string]$Bindings,
    [string]$Contract,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)
$ErrorActionPreference = 'Stop'
$PythonCandidates = @()
if ($env:ART_HARNESS_PYTHON) { $PythonCandidates += $env:ART_HARNESS_PYTHON }
$PythonCandidates += Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($PythonCommand -and $PythonCommand.Source -notmatch 'WindowsApps') { $PythonCandidates += $PythonCommand.Source }

$HarnessArgs = @()
if ($Command) { $HarnessArgs += $Command }
if ($Stage) { $HarnessArgs += @("--stage", $Stage) }
if ($Artifacts) { $HarnessArgs += @("--artifacts", $Artifacts) }
if ($Manifest) { $HarnessArgs += @("--manifest", $Manifest) }
if ($Review) { $HarnessArgs += @("--review", $Review) }
if ($Attestation) { $HarnessArgs += @("--attestation", $Attestation) }
if ($Certificate) { $HarnessArgs += @("--certificate", $Certificate) }
if ($Out) { $HarnessArgs += @("--out", $Out) }
if ($Dependencies) { $HarnessArgs += @("--dependencies", $Dependencies) }
if ($CertificateId) { $HarnessArgs += @("--certificate-id", $CertificateId) }
if ($ApprovalScope) { $HarnessArgs += @("--approval-scope", $ApprovalScope) }
if ($Quality) { $HarnessArgs += @("--quality", $Quality) }
if ($Bindings) { $HarnessArgs += @("--bindings", $Bindings) }
if ($Contract) { $HarnessArgs += @("--contract", $Contract) }
if ($Rest) { $HarnessArgs += $Rest }

$Harness = Join-Path $PSScriptRoot 'tools\art_harness.py'
if (-not (Test-Path -LiteralPath $Harness)) {
    Write-Error ("Harness not found: " + $Harness)
    exit 2
}
foreach ($Candidate in $PythonCandidates) {
    if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
        & $Candidate -X utf8 $Harness @HarnessArgs
        $Code = $LASTEXITCODE
        $Meaning = switch ($Code) {
            0 { "accepted for these exact inputs only" }
            2 { "blocked or invalid inputs" }
            3 { "valid run but not accepted" }
            default { "unexpected exit code" }
        }
        Write-Host ("EXIT_CODE " + $Code + " (" + $Meaning + ")")
        exit $Code
    }
}
throw 'No usable Python. Set ART_HARNESS_PYTHON to Python 3.10+ executable; the WindowsApps alias is not accepted.'
