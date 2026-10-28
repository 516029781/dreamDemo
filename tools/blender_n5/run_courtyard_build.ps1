# Build native courtyard modules, the look scene, the full map and run the verifier.
# Each Blender stage is a separate process with its own log.
#
# Usage (project root):
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\blender\run_courtyard_build.ps1
#   ... -Stage env_tree,map001          # directed build: only these stages
#   ... -Stage env_tree -DryRun         # print the exact commands, run nothing
#
# Defaults keep the previous full 20-stage exit. The first failing stage stops
# the run (failure propagation); its exit code and log gate result are recorded.
param(
    [string[]]$Stage = @(),
    [switch]$DryRun
)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Blender = if ($env:P1_BLENDER_EXE) {
    $env:P1_BLENDER_EXE
} else {
    Join-Path $env:USERPROFILE ".cache\blender\5.2.3\blender-5.2.3-windows-x64\blender.exe"
}
$Python = "C:\Users\tt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$LogDir = Join-Path $PSScriptRoot "logs"
$Summary = Join-Path $LogDir "courtyard_build_summary.log"
$PerfDir = Join-Path $Root "delivery\performance"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$PerfOut = Join-Path $PerfDir ("blender_build_" + $Stamp + ".json")
$Gate = Join-Path $Root "tools\art_gate\build_log_gate.py"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Content -Path $Summary -Value ("courtyard build started " + (Get-Date -Format o)) -Encoding UTF8

$Runs = @(
    @{ Stage = "env_curb"; Script = "build_env_courtyard.py"; Arg = "curb"; Profile = "blender" },
    @{ Stage = "env_low_wall"; Script = "build_env_courtyard.py"; Arg = "low_wall"; Profile = "blender" },
    @{ Stage = "env_railing"; Script = "build_env_courtyard.py"; Arg = "railing"; Profile = "blender" },
    @{ Stage = "env_steps"; Script = "build_env_courtyard.py"; Arg = "steps"; Profile = "blender" },
    @{ Stage = "env_tree"; Script = "build_env_courtyard.py"; Arg = "tree"; Profile = "blender" },
    @{ Stage = "env_ring_planter"; Script = "build_env_courtyard.py"; Arg = "ring_planter"; Profile = "blender" },
    @{ Stage = "env_side_planter"; Script = "build_env_courtyard.py"; Arg = "side_planter"; Profile = "blender" },
    @{ Stage = "env_shrub_a"; Script = "build_env_courtyard.py"; Arg = "shrub_a"; Profile = "blender" },
    @{ Stage = "env_shrub_b"; Script = "build_env_courtyard.py"; Arg = "shrub_b"; Profile = "blender" },
    @{ Stage = "env_dry_grass"; Script = "build_env_courtyard.py"; Arg = "dry_grass"; Profile = "blender" },
    @{ Stage = "env_fallen_leaves"; Script = "build_env_courtyard.py"; Arg = "fallen_leaves"; Profile = "blender" },
    @{ Stage = "prop_pergola"; Script = "build_props_courtyard.py"; Arg = "pergola"; Profile = "blender" },
    @{ Stage = "prop_message_board"; Script = "build_props_courtyard.py"; Arg = "message_board"; Profile = "blender" },
    @{ Stage = "prop_lamp"; Script = "build_props_courtyard.py"; Arg = "lamp"; Profile = "blender" },
    @{ Stage = "prop_direction_sign"; Script = "build_props_courtyard.py"; Arg = "direction_sign"; Profile = "blender" },
    @{ Stage = "prop_postcards"; Script = "build_props_courtyard.py"; Arg = "postcards"; Profile = "blender" },
    @{ Stage = "materials_all"; Script = "build_materials_courtyard.py"; Arg = "all"; Profile = "blender" },
    @{ Stage = "look001"; Script = "build_look001.py"; Arg = ""; Profile = "blender" },
    @{ Stage = "map001"; Script = "build_map001.py"; Arg = ""; Profile = "blender" },
    @{ Stage = "verify"; Script = "verify_courtyard_assets.py"; Arg = ""; Profile = "verify" }
)

if ($Stage.Count -gt 0) {
    $Stage = $Stage | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
    $Known = $Runs | ForEach-Object { $_.Stage }
    $Unknown = $Stage | Where-Object { $Known -notcontains $_ }
    if ($Unknown.Count -gt 0) {
        Write-Error ("Unknown stage(s): " + ($Unknown -join ", ") + ". Known: " + ($Known -join ", "))
        exit 2
    }
    $Selected = $Runs | Where-Object { $Stage -contains $_.Stage }
} else {
    $Selected = $Runs
}

if (-not (Test-Path -LiteralPath $Blender)) {
    Write-Error ("Blender not found: " + $Blender)
    exit 2
}

$Records = @()
$Failed = $false
$OverallStart = Get-Date
foreach ($Run in $Selected) {
    $Log = Join-Path $LogDir ($Run.Stage + ".log")
    $BlenderArgs = @("--background", "--factory-startup", "--python",
                     (Join-Path $PSScriptRoot $Run.Script))
    if ($Run.Arg -ne "") {
        $BlenderArgs += @("--", $Run.Arg)
    }
    if ($DryRun) {
        Write-Host ("DRYRUN {0} -> {1} {2}" -f $Run.Stage, $Blender, ($BlenderArgs -join " "))
        $Records += [ordered]@{ stage = $Run.Stage; dry_run = $true; log = $Log }
        continue
    }

    $Watch = [System.Diagnostics.Stopwatch]::StartNew()
    & $Blender @BlenderArgs *> $Log
    $Code = $LASTEXITCODE
    $Watch.Stop()
    $Seconds = [math]::Round($Watch.Elapsed.TotalSeconds, 3)

    & $Python -X utf8 $Gate --log $Log --profile $Run.Profile --exit-code $Code --json-out ((Join-Path $PerfDir ("gate_" + $Run.Stage + "_" + $Stamp + ".json"))) | Out-Null
    $GateCode = $LASTEXITCODE
    $LogHash = (Get-FileHash -LiteralPath $Log -Algorithm SHA256).Hash.ToLower()

    $Record = [ordered]@{
        stage = $Run.Stage
        exit = $Code
        gate_exit = $GateCode
        seconds = $Seconds
        log = $Log
        log_sha256 = $LogHash
        profile = $Run.Profile
    }
    $Records += $Record
    $Line = "{0} exit={1} gate={2} seconds={3} log={4}" -f $Run.Stage, $Code, $GateCode, $Seconds, $Log
    Write-Host $Line
    Add-Content -Path $Summary -Value $Line -Encoding UTF8

    if ($Code -ne 0 -or $GateCode -ne 0) {
        Add-Content -Path $Summary -Value ("courtyard build STOPPED at " + $Run.Stage) -Encoding UTF8
        $Failed = $true
        break
    }
}

$Elapsed = [math]::Round(((Get-Date) - $OverallStart).TotalSeconds, 3)
if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $PerfDir | Out-Null
    $Report = [ordered]@{
        kind = "directed_blender_build_run"
        started_at = $OverallStart.ToString("o")
        elapsed_seconds = $Elapsed
        requested_stages = $Stage
        selected_count = $Selected.Count
        failed = $Failed
        records = $Records
        meaning = "Stage timing only; a pass is not art approval and excludes review waiting."
    }
    $Report | ConvertTo-Json -Depth 6 | Set-Content -Path $PerfOut -Encoding UTF8
    Add-Content -Path $Summary -Value ("courtyard build finished " + (Get-Date -Format o) + " report=" + $PerfOut) -Encoding UTF8
    Write-Host ("BUILD_REPORT " + $PerfOut)
}

Get-Content -Path $Summary
if ($Failed) { exit 1 }
exit 0
