@echo off
>nul 2>&1 net session
if %errorlevel% neq 0 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
  exit /b
)
set arg=%~1
if /i "%arg%"=="all" (
  powershell -NoProfile -Command "Get-Process | Where-Object { $_.Name -notin @('Idle','System','Registry','smss','csrss','wininit','winlogon','services','lsass','svchost','fontdrvhost','dwm') } | Stop-Process -Force -ErrorAction SilentlyContinue"
  exit /b 0
)
if /i "%arg%"=="ports" (
  for %%P in (5173 8000) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R /C:":%%P[ ]"') do taskkill /F /PID %%A >nul 2>&1
  )
  exit /b 0
)
for %%I in (node.exe npm.exe npx.exe vite.exe python.exe pythonw.exe uvicorn.exe gunicorn.exe streamlit.exe playwright.exe) do taskkill /F /IM %%I /T >nul 2>&1
taskkill /F /FI "USERNAME eq %USERNAME%" /FI "IMAGENAME ne cmd.exe" /FI "IMAGENAME ne conhost.exe" /FI "IMAGENAME ne powershell.exe" /FI "IMAGENAME ne explorer.exe" /T >nul 2>&1
exit /b 0
