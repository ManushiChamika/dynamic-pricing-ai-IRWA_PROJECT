@echo off
echo.
echo ================================================
echo   Dynamic Pricing AI - Full Stack Launcher
echo ================================================
echo.

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)
echo [OK] Python found

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found
    pause
    exit /b 1
)
echo [OK] Node.js found
echo.

REM Kill existing processes
echo Cleaning up old processes...
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] Cleanup complete
echo.

REM Check dependencies
echo Checking dependencies...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing Python packages...
    pip install -r requirements.txt
)

if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)
echo [OK] Dependencies ready
echo.

REM Start servers
echo Starting Backend API (port 8000)...
start "Backend API" cmd /k "python -m uvicorn backend.main:app --reload --port 8000 --host 127.0.0.1"

timeout /t 3 /nobreak >nul

echo Starting Frontend Dev Server (port 5173)...
start "Frontend Dev" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ================================================
echo   SERVERS STARTED!
echo ================================================
echo.
echo   Frontend: http://localhost:5173
echo   Backend:  http://127.0.0.1:8000
echo   API Docs: http://127.0.0.1:8000/docs
echo.
echo ================================================
echo.

pause
