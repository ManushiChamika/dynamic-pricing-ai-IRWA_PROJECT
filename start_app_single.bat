@echo off
setlocal enableextensions
title Dynamic Pricing AI - All Services
cd /d "%~dp0"

echo ========================================
echo   Dynamic Pricing AI - All Services
echo ========================================
echo.

rem Kill any existing processes on these ports
echo Stopping any existing services...
netstat -ano | findstr :8000 | for /f "tokens=5" %%a in ('findstr /r /c:"[0-9]*"') do taskkill /f /pid %%a >nul 2>&1
netstat -ano | findstr :8501 | for /f "tokens=5" %%a in ('findstr /r /c:"[0-9]*"') do taskkill /f /pid %%a >nul 2>&1
netstat -ano | findstr :5173 | for /f "tokens=5" %%a in ('findstr /r /c:"[0-9]*"') do taskkill /f /pid %%a >nul 2>&1

echo.
echo Starting all services...
echo - FastAPI: http://localhost:8000
echo - Streamlit: http://localhost:8501
echo - Frontend: http://localhost:5173
echo.
echo Press Ctrl+C to stop all services
echo.

rem Start FastAPI in background
start /b "FastAPI" ".venv\Scripts\python.exe" -m uvicorn backend.main:app --reload --port 8000

rem Wait a moment
timeout /t 2 /nobreak >nul

rem Start Streamlit in background  
start /b "Streamlit" ".venv\Scripts\python.exe" -m streamlit run app/streamlit_app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false

rem Wait a moment
timeout /t 2 /nobreak >nul

rem Start Frontend in background
cd frontend
start /b "Frontend" npm run dev -- --port 5173 --host 0.0.0.0
cd..

echo All services started. Check the URLs above.
echo.
echo To stop services, press Ctrl+C or close this window.
echo.

rem Keep the window open
:loop
timeout /t 5 /nobreak >nul
goto loop