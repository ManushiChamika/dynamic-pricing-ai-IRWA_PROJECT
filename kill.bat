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
taskkill /F /FI "USERNAME eq %USERNAME%" /FI "IMAGENAME ne cmd.exe" /FI "IMAGENAME ne conhost.exe" /FI "IMAGENAME ne powershell.exe" /FI "IMAGENAME ne explorer.exe" /T >nul 2>&1
exit /b 0
