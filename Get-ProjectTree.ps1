<#
  Usage:
    .\Get-ProjectTree.ps1 -Root "C:\path\to\repo" -MaxSizeMB 5 -DryRun

  Outputs a list (one relative path per line). Use -DryRun to preview only.
#>

param(
  [string]$Root = (Get-Location).Path,
  [string[]]$ExcludeDirs = @(
    'node_modules', '.git', 'venv', '.venv', 'env', '__pycache__',
    'dist', 'build', 'site-packages', '.egg-info', 'vendor'
  ),
  [string[]]$AllowedExts = @(
    '.py', '.md', '.txt', '.json', '.yml', '.yaml', '.ini', '.cfg', '.js',
    '.ts', '.html', '.css', '.java', '.c', '.cpp', '.h', '.rb', '.go', '.rs',
    '.sh', '.ps1', '.sql'
  ),
  [int]$MaxSizeMB = 5,
  [switch]$DryRun
)

# --- helpers ---------------------------------------------------------------
function Is-TextFile {
  param([string]$Path)
  try {
    $bytes = Get-Content -Path $Path -Encoding Byte -TotalCount 1024 `
      -ErrorAction Stop
    # If any NUL (0) found in the first chunk, treat as binary
    return -not ($bytes -contains 0)
  } catch {
    return $false
  }
}

# Build exclusion regex for directories
$esc = $ExcludeDirs | ForEach-Object { [regex]::Escape($_) }
$dirPattern = ($esc -join '|')
$dirRegex = "\\($dirPattern)\\"

# special file names without extension we want to allow
$allowedNames = @('README.md', 'requirements.txt', 'me.md')
$maxBytes = $MaxSizeMB * 1MB
$rootTrim = $Root.TrimEnd('\','/')

Write-Verbose "Root: $Root"
Write-Verbose "Excluding dirs: $($ExcludeDirs -join ', ')"

# --- collect files --------------------------------------------------------
$allFiles = Get-ChildItem -Path $Root -Recurse -File `
  -ErrorAction SilentlyContinue

$filtered = $allFiles | Where-Object {
  $full = $_.FullName
  # skip if inside excluded directory
  if ($full -match $dirRegex) { return $false }

  # skip very large files
  if ($_.Length -gt $maxBytes) { return $false }

  # allow if filename explicitly whitelisted
  if ($allowedNames -contains $_.Name.ToLower()) { return $true }

  # allow by extension
  if ($AllowedExts -contains $_.Extension.ToLower()) {
    # simple NUL-byte test for binary files
    return (Is-TextFile -Path $full)
  }
  return $false
}

# produce relative paths and optional nice tree-like indenting
$relList = @()
foreach ($f in $filtered | Sort-Object FullName) {
  $rel = $f.FullName.Substring($rootTrim.Length).TrimStart('\','/')
  $relList += $rel
}

# --- output ---------------------------------------------------------------
if ($DryRun) {
  Write-Output "DRY-RUN: would include $($relList.Count) files:"
  $relList | ForEach-Object { Write-Output $_ }
} else {
  # default to printing list to stdout; user can redirect to file
  $relList | ForEach-Object { Write-Output $_ }
}

# Summary to stderr for scripts to capture
[Console]::Error.WriteLine("Included: $($relList.Count)  " +
  "Scanned: $($allFiles.Count)")
