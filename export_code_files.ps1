param(
    [string]$Name = "default"
)

# Get current git branch
$branch = git rev-parse --abbrev-ref HEAD 2>$null
if (-not $branch) { $branch = "no-branch" }

# Set output file name
$outputFile = "all_code_files_${branch}_$Name.txt"

# Remove the output file if it already exists
if (Test-Path $outputFile) { Remove-Item $outputFile }

# Define file extensions to include
$includeExtensions = @("*.py", "*.md", "*.txt")

# Get all code files recursively, excluding unnecessary files and folders
$codeFiles = Get-ChildItem -Path . -Recurse -Include $includeExtensions -File |
    Where-Object {
        $_.FullName -notmatch "__pycache__|\.venv|\.git|env|Lib|site-packages|\.pyc$|\.pyo$|\.db$"
    }

foreach ($file in $codeFiles) {
    Add-Content -Path $outputFile -Value "===== $($file.FullName) ====="
    Get-Content $file.FullName | Add-Content -Path $outputFile
    Add-Content -Path $outputFile -Value "`n"
}

Write-Host "All code files have been combined into $outputFile"
