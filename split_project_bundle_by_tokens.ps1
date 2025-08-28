<#
Splits a project bundle file (created by collect_project_code.ps1) into parts
keeping entire file blocks (headers like: === File: path ===) intact.

Defaults:
- InputFile: project_code_bundle.txt
- OutputPrefix: project_code_bundle_part
- TokenLimit: 30000 (soft estimate)
- CharPerToken: 4 (approx chars per token)

Behavior:
- Does not split an individual file block across parts even if it exceeds the token limit.
- Starts a new part only between file blocks.
- Writes UTF-8 (no BOM).
- DryRun prints what would be created.
#>
param(
    [string]$InputFile = "project_code_bundle.txt",
    [string]$OutputPrefix = "project_code_bundle_part",
    [int]$TokenLimit = 30000,
    [int]$CharPerToken = 4,
    [string]$LogFile = "split_project_bundle.log",
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Log($m) {
    $line = "[{0}] {1}" -f (Get-Date), $m
    Add-Content -Path $LogFile -Value $line
}

if (-not (Test-Path $InputFile)) {
    Write-Host "Input file '$InputFile' not found." -ForegroundColor Red
    exit 1
}

# Read all lines preserving newlines
$content = Get-Content -Path $InputFile -Raw -Encoding UTF8 -ErrorAction Stop -ReadCount 0
# Normalize newlines to LF for reliable regex operations
$content = $content -replace "\r\n", "\n"

# Split into blocks by locating header positions using explicit regex matches.
# This avoids edge cases with Split and preserves block boundaries precisely.
$headerRegex = '(?m)^=== File: .* ===\r?$'
$mMatches = [regex]::Matches($content, $headerRegex)
$blocks = @()

if ($mMatches.Count -eq 0) {
    # No headers found, treat whole file as single block
    $blocks += $content
} else {
    for ($i = 0; $i -lt $mMatches.Count; $i++) {
        $start = $mMatches[$i].Index
        $end = if ($i -lt $mMatches.Count - 1) { $mMatches[$i+1].Index - 1 } else { $content.Length - 1 }
        $len = $end - $start + 1
        $block = $content.Substring($start, $len)
        $block = $block.TrimEnd("`n", "`r")
        $blocks += $block
    }
}

if ($DryRun) { Write-Host "Found $($blocks.Count) blocks (file blocks) in '$InputFile'.`n" }

$currentPart = 1
$currentTokens = 0
$currentLines = 0
$currentBlocks = @()
$created = 0

for ($i = 0; $i -lt $blocks.Count; $i++) {
    $block = $blocks[$i]
    # Ensure block uses LF; we'll restore CRLF on write
    $block = $block -replace "\r\n", "\n"
    $blockLengthChars = $block.Length
    $blockTokens = [math]::Ceiling($blockLengthChars / [double]$CharPerToken)
    $blockLines = ($block -split "\n").Count

    if ($DryRun) {
        Write-Host "Block $($i+1): tokens~$blockTokens, lines=$blockLines"
    }

    $wouldExceed = ($currentTokens + $blockTokens) -gt $TokenLimit

    if ($wouldExceed -and $currentBlocks.Count -gt 0) {
        # flush current part
        $outName = "${OutputPrefix}${currentPart}.txt"
        if ($DryRun) {
            Write-Host "Would write part $currentPart with $($currentBlocks.Count) blocks, tokens~$currentTokens -> $outName"
        } else {
            $text = ($currentBlocks -join "\n\n") -replace "\n", "`r`n"
            # write without BOM
            [System.IO.File]::WriteAllText((Join-Path (Get-Location) $outName), $text, (New-Object System.Text.UTF8Encoding($false)))
            Log "Wrote $outName (blocks=$($currentBlocks.Count), tokens~$currentTokens)"
            $created++
        }
        $currentPart++
        $currentTokens = 0
        $currentLines = 0
        $currentBlocks = @()
    }

    # add block to current part
    $currentBlocks += $block
    $currentTokens += $blockTokens
    $currentLines += $blockLines

    # If this single block alone exceeds the limit and current part only contains it, that's allowed (soft limit)
}

# write remaining
if ($currentBlocks.Count -gt 0) {
    $outName = "${OutputPrefix}${currentPart}.txt"
    if ($DryRun) {
        Write-Host "Would write part $currentPart with $($currentBlocks.Count) blocks, tokens~$currentTokens -> $outName"
    } else {
        $text = ($currentBlocks -join "\n\n") -replace "\n", "`r`n"
        [System.IO.File]::WriteAllText((Join-Path (Get-Location) $outName), $text, (New-Object System.Text.UTF8Encoding($false)))
        Log "Wrote $outName (blocks=$($currentBlocks.Count), tokens~$currentTokens)"
        $created++
    }
}

if ($DryRun) {
    Write-Host "Dry run complete. No files written."
} else {
    Write-Host "Done. Created $created files (prefix: $OutputPrefix). See $LogFile for details."
}
