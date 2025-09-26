# PowerShell script to start both servers
Write-Host "Installing backend dependencies..." -ForegroundColor Green
py -3.11 -m pip install -r requirements.txt

Write-Host "Installing frontend dependencies..." -ForegroundColor Green
Set-Location frontend
npm install
Set-Location ..

Write-Host "Starting backend server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "py -3.11 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Normal

Write-Host "Waiting 3 seconds for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Starting frontend server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location frontend; npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "Both servers are starting in separate windows:" -ForegroundColor Cyan
Write-Host "- Backend: http://localhost:8000" -ForegroundColor White
Write-Host "- Frontend: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")