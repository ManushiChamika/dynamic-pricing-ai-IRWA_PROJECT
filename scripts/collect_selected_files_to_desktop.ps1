# Concatenate selected project files into a single text file on the current user's Desktop
# Usage: run from repository root or anywhere; script resolves repository root relative to its location

param(
    [string] $OutputFileName = "selected_project_files.txt"
)

# Resolve script and repo root
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Parent $scriptPath
# Assume script is in <repo>/scripts; repo root is parent of scripts
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")

# List of relative paths to collect (as requested)
$files = @(
    "app/llm_client.py",
    "core/agents/pricing_optimizer.py",
    "core/agents/supervisor.py",
    "core/agents/market_collector.py",
    "core/agents/data_collector/collector.py",
    "core/agents/data_collector/connectors/mock.py",
    "core/agents/alert_service/schemas.py",
    "scripts/smoke_data_collector.py",
    "scripts/smoke_price_optimizer.py"
)

# Output path on current user's Desktop
$desktop = [Environment]::GetFolderPath('Desktop')
$outPath = Join-Path $desktop $OutputFileName

# Prepare output file (overwrite if exists)
try {
    "" | Out-File -FilePath $outPath -Encoding utf8
} catch {
    Write-Error "Failed to create output file: $_"
    exit 2
}

foreach ($rel in $files) {
    $abs = Join-Path $repoRoot $rel
    if (-not (Test-Path $abs)) {
        Write-Warning "Missing file: $rel (resolved: $abs). Skipping."
        continue
    }

    # Write a header between files
    $header = "=== File: $rel ==="
    Add-Content -Path $outPath -Value $header -Encoding utf8

    try {
        Get-Content -Path $abs -Encoding utf8 | Add-Content -Path $outPath -Encoding utf8
    } catch {
        Write-Warning "Could not read $($rel): $($_)"
        continue
    }

    # Add blank line after each file
    Add-Content -Path $outPath -Value "`r`n" -Encoding utf8
}

Write-Output "Wrote combined file to: $outPath"
