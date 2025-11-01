@echo off
echo Starting Dynamic Pricing AI Application...
echo.

REM Change to the project directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install packages
        pause
        exit /b 1
    )
)

REM Find an available port (try 8000, then 8001, then 8002)
set PORT=8000
echo Checking port %PORT%...
netstat -an | find ":%PORT%" >nul
if not errorlevel 1 (
    set PORT=8001
    echo Port 8000 is busy, trying %PORT%...
    netstat -an | find ":%PORT%" >nul
    if not errorlevel 1 (
        set PORT=8002
        echo Port 8001 is busy, trying %PORT%...
    )
)

echo.
echo ========================================
echo  Dynamic Pricing AI Application
echo ========================================
echo.
echo Starting server on port %PORT%...
echo.
echo Once started, open your browser to:
echo   http://127.0.0.1:%PORT%
echo.
echo NOTE: For hot-reload dev mode, use run_full_app.bat
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the FastAPI server
python -m uvicorn backend.main:app --reload --port %PORT% --host 127.0.0.1

REM If server stops, pause so user can see any error messages
echo.
echo Server stopped.
pause