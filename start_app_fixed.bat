@echo off
setlocal enableextensions
title Dynamic Pricing AI - Dev Launcher
cd /d "%~dp0"

echo ========================================
echo   Dynamic Pricing AI - Dev Launcher
echo ========================================
echo.

echo Starting FastAPI backend...
start "FastAPI Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000"

timeout /t 2 /nobreak >nul

echo Starting Streamlit dashboard...
start "Streamlit Dashboard" cmd /k ".venv\Scripts\python.exe -m streamlit run app/streamlit_app.py --server.port 8501"

timeout /t 2 /nobreak >nul

echo Starting frontend...
start "Frontend" cmd /k "cd /d \"%~dp0frontend\" && npm run dev -- --port 5173"

echo.
echo All services started in separate windows:
echo - FastAPI: http://localhost:8000
echo - Streamlit: http://localhost:8501  
echo - Frontend: http://localhost:5173
echo.
echo Press any key to exit...
pause >nul