@echo off
echo Starting Full Dynamic Pricing AI Application...
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

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if required Python packages are installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing Python packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install Python packages
        pause
        exit /b 1
    )
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
    cd ..
)

REM Find available ports
set BACKEND_PORT=8000
set FRONTEND_PORT=5174

echo Checking backend port %BACKEND_PORT%...
netstat -an | find ":%BACKEND_PORT%" >nul
if not errorlevel 1 (
    set BACKEND_PORT=8001
    echo Port 8000 is busy, trying %BACKEND_PORT%...
)

echo.
echo ========================================
echo  Dynamic Pricing AI - Full Stack
echo ========================================
echo.
echo Starting Backend on port %BACKEND_PORT%...
echo Starting Frontend on port %FRONTEND_PORT%...
echo.
echo Once started, open your browser to:
echo   Frontend (React): http://localhost:%FRONTEND_PORT%
echo   Backend API:      http://127.0.0.1:%BACKEND_PORT%
echo.
echo Press Ctrl+C in either window to stop
echo ========================================
echo.

REM Start backend in a new window
start "Backend API" cmd /k "python -m uvicorn backend.main:app --reload --port %BACKEND_PORT% --host 127.0.0.1"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
start "Frontend Dev Server" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are starting...
echo Check the new windows for server output
echo.
pause
