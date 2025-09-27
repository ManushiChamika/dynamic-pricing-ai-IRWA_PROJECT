# Dynamic Pricing AI - Single Terminal Launcher
# Run with: powershell -ExecutionPolicy Bypass -File start_app_single.ps1

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Dynamic Pricing AI - All Services" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kill existing processes on these ports
Write-Host "Stopping any existing services..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000,8501,5173 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Starting all services (press Ctrl+C to stop all)..." -ForegroundColor Green
Write-Host "- FastAPI: http://localhost:8000" -ForegroundColor White
Write-Host "- Streamlit: http://localhost:8501" -ForegroundColor White  
Write-Host "- Frontend: http://localhost:5173" -ForegroundColor White
Write-Host ""

# Start all services as background jobs
$jobs = @()
$jobs += Start-Job -ScriptBlock { 
    Set-Location $using:PSScriptRoot
    & '.venv\Scripts\python.exe' -m uvicorn backend.main:app --reload --port 8000
} -Name 'FastAPI'

$jobs += Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot  
    & '.venv\Scripts\python.exe' -m streamlit run app/streamlit_app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
    $env:STREAMLIT_BROWSER_GATHERUSAGESTATS = "false"
} -Name 'Streamlit'

$jobs += Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\frontend"
    npm run dev -- --port 5173 --host 0.0.0.0
} -Name 'Frontend'

# Monitor and display output from all jobs
try {
    while ($jobs | Where-Object { $_.State -eq 'Running' }) {
        foreach ($job in $jobs) {
            $output = Receive-Job $job -ErrorAction SilentlyContinue
            if ($output) {
                $color = switch ($job.Name) {
                    'FastAPI' { 'Blue' }
                    'Streamlit' { 'Magenta' }  
                    'Frontend' { 'Green' }
                    default { 'White' }
                }
                Write-Host "[$($job.Name)] " -ForegroundColor $color -NoNewline
                Write-Host $output
            }
        }
        Start-Sleep -Milliseconds 200
    }
} finally {
    Write-Host "`nStopping all services..." -ForegroundColor Red
    $jobs | Stop-Job -PassThru | Remove-Job
}