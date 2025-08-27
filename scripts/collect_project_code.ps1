<#
Collect project source files into a single text file with metadata.
- Excludes: __pycache__, .git, node_modules, venvs, binary files, common DB and image files
- Includes common source/text extensions and attempts to include text files without extension
- Skips files larger than MaxFileSizeMB (default 10 MB) to avoid excessive output

Usage (PowerShell):
  pwsh ./scripts/collect_project_code.ps1 -RootPath . -OutFile project_code_dump.txt

Parameters:
  -RootPath: directory to scan (default: current directory)
  -OutFile: output file path (default: ./project_code_dump.txt)
  -MaxFileSizeMB: skip files larger than this (default: 10)
  -Verbose: show progress

#>
[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$RootPath = ".",

    [Parameter(Position=1)]
    [string]$OutFile = "project_code_dump.txt",

    [int]$MaxFileSizeMB = 10
)

# Resolve paths
$RootPath = (Resolve-Path -Path $RootPath).ProviderPath
$OutFile = Join-Path -Path (Get-Location) -ChildPath $OutFile

# Exclude directories and file extensions
$ExcludeDirs = @('.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env', 'build', 'dist', '.ipynb_checkpoints')
$AllowedExts = @('.py', '.md', '.txt', '.json', '.yaml', '.yml', '.ipynb', '.html', '.htm', '.css', '.js', '.ts', '.jsx', '.tsx', '.pyi', '.cfg', '.ini', '.toml', '.rst', '.sql', '.ps1', '.psm1')
$ExcludeExts = @('.pyc', '.pyo', '.so', '.dll', '.exe', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.db', '.sqlite', '.class', '.jar', '.zip', '.tar', '.gz')

# Convert max size to bytes
$MaxFileSizeBytes = $MaxFileSizeMB * 1MB

function IsTextFile([string]$path) {
    try {
        $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read)
        try {
            $buffer = New-Object byte[] (4096)
            $bytesRead = $fs.Read($buffer, 0, $buffer.Length)
            if ($bytesRead -le 0) { return $true }
            for ($i=0; $i -lt $bytesRead; $i++) {
                if ($buffer[$i] -eq 0) { return $false }
            }
            return $true
        } finally { $fs.Close() }
    } catch {
        return $false
    }
}

function Write-Header($stream, $relPath, $fileInfo, $hash) {
    $stream.WriteLine("==== FILE: $relPath ====")
    $stream.WriteLine("SizeBytes: $($fileInfo.Length)")
    $stream.WriteLine("LastWriteTime: $($fileInfo.LastWriteTimeUtc.ToString('u')) UTC")
    $stream.WriteLine("SHA256: $hash")
    $stream.WriteLine("---- START CONTENT ----")
}

function Write-Footer($stream) {
    $stream.WriteLine("---- END CONTENT ----")
    $stream.WriteLine("`n")
}

# Gather files
Write-Verbose "Scanning $RootPath..."
$files = Get-ChildItem -Path $RootPath -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    # Exclude hidden/system mount points by path
    $full = $_.FullName
    foreach ($d in $ExcludeDirs) { if ($full -like "*\$d\*") { return $false } }

    # Exclude by extension
    $ext = $_.Extension.ToLower()
    if ($ExcludeExts -contains $ext) { return $false }

    # Allow known text extensions; also allow files without extension for inspection
    if ($ext -and -not ($AllowedExts -contains $ext)) {
        return $false
    }
    return $true
}

# Sort file list for reproducible output
$files = $files | Sort-Object FullName

# Prepare output stream (UTF8 without BOM)
$fsOut = New-Object System.IO.StreamWriter($OutFile, $false, (New-Object System.Text.UTF8Encoding($false)))
try {
    $fsOut.WriteLine("Project code dump generated: $(Get-Date -Format o)")
    $fsOut.WriteLine("RootPath: $RootPath")
    $fsOut.WriteLine("FileCount: $($files.Count)")
    $fsOut.WriteLine("MaxFileSizeMB: $MaxFileSizeMB")
    $fsOut.WriteLine("`n")

    foreach ($f in $files) {
        try {
            if ($f.Length -gt $MaxFileSizeBytes) {
                Write-Verbose "Skipping (size) $($f.FullName) [$($f.Length) bytes]"
                continue
            }

            # If extension is known text or no extension, check for binary content
            if (-not (IsTextFile $f.FullName)) {
                Write-Verbose "Skipping (binary) $($f.FullName)"
                continue
            }

            $rel = $f.FullName.Substring($RootPath.Length).TrimStart('\')
            $hash = (Get-FileHash -Path $f.FullName -Algorithm SHA256 -ErrorAction SilentlyContinue).Hash
            if (-not $hash) { $hash = '' }

            Write-Verbose "Adding: $rel"
            Write-Header $fsOut $rel $f $hash

            # Read content with safe encoding fallback
            $content = $null
            try {
                $content = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction Stop -Encoding UTF8
            } catch {
                try { $content = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction Stop -Encoding Default } catch { $content = "[UNREADABLE: could not decode file]" }
            }

            try {
                # Ensure content is string for writing
                if ($null -eq $content) { $content = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue }
            } catch { $content = "[UNREADABLE: could not read file]" }

            $fsOut.WriteLine($content)
            Write-Footer $fsOut
        } catch {
            Write-Verbose "Error processing $($f.FullName): $_"
            continue
        }
    }
    Write-Verbose "Wrote output to $OutFile"
} finally {
    $fsOut.Close()
}

Write-Output "Done. Output: $OutFile"
