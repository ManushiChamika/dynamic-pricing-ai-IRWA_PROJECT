@echo off
echo Installing backend dependencies...
py -3.11 -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install backend dependencies
    pause
    exit /b 1
)

echo Installing frontend dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo Failed to install frontend dependencies
    pause
    exit /b 1
)
cd ..

echo Starting backend...
start "Backend Server" cmd /k "py -3.11 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul

echo Starting frontend...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo Both services are starting in separate windows:
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:5173
echo.
echo Press any key to continue...
pause >nul