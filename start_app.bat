@echo off
setlocal enableextensions
title Dynamic Pricing AI - Dev Launcher
cd /d "%~dp0"

rem ---- Configurable ports ----
set STREAMLIT_PORT=8501
set API_PORT=8000
set VITE_PORT=5173

rem ---- Paths ----
set VENV_PY=.\.venv\Scripts\python.exe
set VENV_PIP=.\.venv\Scripts\pip.exe

rem ---- Pre-flight checks ----
if not exist "%VENV_PY%" (
  echo ERROR: Virtual environment not found at .venv
  echo Create it:  python -m venv .venv
  echo Then:       %VENV_PIP% install -r requirements.txt
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo ERROR: npm not found. Install Node.js from https://nodejs.org/
  pause
  exit /b 1
)

rem ---- Frontend deps (first run convenience) ----
if not exist "frontend\node_modules" (
  echo Installing frontend dependencies (npm ci)...
  pushd frontend
  npm ci || npm install
  popd
)

echo ========================================
echo   Dynamic Pricing AI - Dev Launcher
echo ========================================
echo.
echo URLs:
echo - Streamlit: http://localhost:%STREAMLIT_PORT%
echo - FastAPI  : http://localhost:%API_PORT%  (docs: http://localhost:%API_PORT%/docs)
echo - Vite     : http://localhost:%VITE_PORT%
echo.

rem ---- Start FastAPI (Uvicorn) ----
start "FastAPI (Uvicorn) :%API_PORT%" cmd /k ^
  "%VENV_PY%" -m uvicorn backend.main:app --reload --port %API_PORT%

rem ---- Start Streamlit Dashboard ----
start "Streamlit Dashboard :%STREAMLIT_PORT%" cmd /k ^
  "%VENV_PY%" -m streamlit run app/streamlit_app.py --server.headless true --server.port %STREAMLIT_PORT% --browser.gatherUsageStats false

rem ---- Start Vite Frontend ----
start "Vite Dev Server :%VITE_PORT%" cmd /k ^
  "cd /d \"%~dp0frontend\" && npm run dev -- --port %VITE_PORT%"

echo.
echo All services launched in separate windows.
echo Close those windows to stop services.
echo Press any key to exit this launcher...
pause >nul