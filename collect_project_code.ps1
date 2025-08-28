param(
    [string]$OutputFile = "project_code_bundle.txt",
    [string]$LogFile = "project_code_bundle.log",
    [int]$MaxSizeMB = 5,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$MaxSizeBytes = $MaxSizeMB * 1MB
$Included = 0
$Skipped = 0
$Errors = 0
[int]$WordLimit = 25000
[int]$LineLimit = 50000
[int]$Part = 1
[int]$CurrentWords = 0
[int]$CurrentLines = 0
[string]$CurrentOutputFile = $OutputFile

# List of text file extensions
$textExts = @(
    ".py",".md",".txt",".json",".yaml",".yml",".ini",".cfg",".js",".ts",".html",".css",
    ".java",".c",".cpp",".h",".rb",".go",".rs",".sh",".ps1",".sql"
)

# List of excluded folders
$excludeDirs = @(
    ".git","__pycache__","build","dist","node_modules","venv",".venv","env",
    "site-packages",".egg-info",".parcel-cache","vendor"
)

function IsTextFile($path) {
    try {
        $bytes = Get-Content -Path $path -Encoding Byte -ReadCount 0
        if ($bytes -contains 0) { return $false }
        $null = [System.Text.Encoding]::UTF8.GetString($bytes)
        return $true
    } catch {
        try {
            $null = Get-Content -Path $path -Encoding Default -ErrorAction Stop
            return $true
        } catch {
            return $false
        }
    }
}

function ShouldExclude($path) {
    foreach ($dir in $excludeDirs) {
        if ($path -match "(^|\\)$dir(\\|$)") { return $true }
    }
    return $false
}

function Log($msg) {
    Add-Content -Path $LogFile -Value ("[{0}] {1}" -f (Get-Date), $msg)
}

# Find all files
$files = Get-ChildItem -Path . -Recurse -File | Where-Object {
    -not (ShouldExclude($_.FullName)) -and
    ($textExts -contains $_.Extension.ToLower() -or $_.Name -eq "requirements.txt" -or $_.Name -eq "README.md")
}

if ($DryRun) {
    foreach ($file in $files) {
        if ($file.Length -gt $MaxSizeBytes) {
            Write-Host "SKIP (large): $($file.FullName)"
            continue
        }
        if (-not (IsTextFile($file.FullName))) {
            Write-Host "SKIP (binary): $($file.FullName)"
            continue
        }
        Write-Host "INCLUDE: $($file.FullName)"
    }
    Write-Host "Dry run complete."
    exit
}

# Clear output files
Set-Content -Path $OutputFile -Value ""
Set-Content -Path $LogFile -Value ""

foreach ($file in $files) {
    $relPath = $file.FullName.Substring((Get-Location).Path.Length + 1)
    if ($file.Length -gt $MaxSizeBytes) {
        Log "SKIP (large > $MaxSizeMB MB): $relPath"
        $Skipped++
        continue
    }
    if (-not (IsTextFile($file.FullName))) {
        Log "SKIP (binary/non-text): $relPath"
        $Skipped++
        continue
    }
    try {
        $header = "=== File: $relPath ==="
        $content = Get-Content -Path $file.FullName -Encoding UTF8
        $fileWords = ($content -join ' ' -split '\s+').Count
        $fileLines = $content.Count

        # Check if adding this file would exceed the limits
        if (($CurrentWords + $fileWords) -gt $WordLimit -or ($CurrentLines + $fileLines) -gt $LineLimit) {
            $Part++
            $CurrentOutputFile = [System.IO.Path]::ChangeExtension($OutputFile, "_part$Part.txt")
            $CurrentWords = 0
            $CurrentLines = 0
        }

        Add-Content -Path $CurrentOutputFile -Value $header
        $content | Add-Content -Path $CurrentOutputFile
        Add-Content -Path $CurrentOutputFile -Value ""
        $Included++
        $CurrentWords += $fileWords
        $CurrentLines += $fileLines
    } catch {
        Log "ERROR: $relPath - $_"
        $Errors++
    }
}

Log "Summary: Included=$Included, Skipped=$Skipped, Errors=$Errors"
Write-Host "Done. Included: $Included, Skipped: $Skipped, Errors: $Errors"
Write-Host "See $LogFile for details."
