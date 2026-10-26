# Read-only probe for an existing Cocos Creator / Cocos Dashboard installation.
# Writes findings as JSON to stdout. Does not install or modify anything.
$ErrorActionPreference = 'SilentlyContinue'

$candidates = New-Object System.Collections.Generic.List[string]

# Common explicit directories
$explicit = @(
  'C:\Program Files\CocosCreator',
  'C:\Program Files (x86)\CocosCreator',
  'C:\Program Files\Cocos',
  'C:\CocosDashboard',
  'C:\CocosCreator',
  "$env:LOCALAPPDATA\Programs\CocosCreator",
  "$env:LOCALAPPDATA\CocosDashboard",
  "$env:APPDATA\CocosDashboard",
  "$env:USERPROFILE\.CocosCreator",
  "$env:USERPROFILE\.CocosDashboard",
  'C:\ProgramData\cocos',
  'C:\ProgramData\cocos\editors',
  'C:\ProgramData\CocosDashboard'
)
foreach ($p in $explicit) { if (Test-Path -LiteralPath $p) { $candidates.Add($p) } }

# Search for CocosCreator.exe in likely roots (bounded depth)
$roots = @('C:\Program Files', 'C:\Program Files (x86)', $env:LOCALAPPDATA, $env:APPDATA, 'C:\ProgramData', 'C:\CocosDashboard')
$exeHits = @()
foreach ($root in $roots) {
  if (Test-Path -LiteralPath $root) {
    $exeHits += Get-ChildItem -LiteralPath $root -Filter 'CocosCreator.exe' -Recurse -Depth 5 -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
  }
}

# Registry uninstall entries
$regPaths = @(
  'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
$regHits = @()
foreach ($rp in $regPaths) {
  $regHits += Get-ItemProperty -Path $rp -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -match 'Cocos' } |
    Select-Object DisplayName, DisplayVersion, InstallLocation, UninstallString
}

# Start menu shortcuts
$smRoots = @('C:\ProgramData\Microsoft\Windows\Start Menu\Programs', "$env:APPDATA\Microsoft\Windows\Start Menu\Programs")
$smHits = @()
foreach ($sm in $smRoots) {
  if (Test-Path -LiteralPath $sm) {
    $smHits += Get-ChildItem -LiteralPath $sm -Recurse -Filter '*Cocos*' -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
  }
}

# App Paths / PATH
$pathHits = @()
$env:PATH -split ';' | ForEach-Object {
  if ($_ -match 'cocos') { $pathHits += $_ }
}
$appPaths = @()
foreach ($k in @('HKLM:\Software\Microsoft\Windows\CurrentVersion\App Paths\CocosCreator.exe','HKCU:\Software\Microsoft\Windows\CurrentVersion\App Paths\CocosCreator.exe')) {
  $v = Get-ItemProperty -Path $k -ErrorAction SilentlyContinue
  if ($v) { $appPaths += $v.'(default)' }
}

$result = [ordered]@{
  probed_at        = (Get-Date).ToString('o')
  explicit_dirs    = $candidates
  exe_hits         = [System.Collections.Generic.List[string]]@($exeHits | Select-Object -Unique)
  registry_hits    = $regHits
  start_menu_hits  = [System.Collections.Generic.List[string]]$smHits
  path_hits        = [System.Collections.Generic.List[string]]$pathHits
  app_paths        = [System.Collections.Generic.List[string]]$appPaths
  found            = (($exeHits.Count + $regHits.Count + $smHits.Count) -gt 0)
}
$result | ConvertTo-Json -Depth 6
