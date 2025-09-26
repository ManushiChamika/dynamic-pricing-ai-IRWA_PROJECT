@echo off
title Dynamic Pricing AI - Web App
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please create a virtual environment first.
    pause
    exit /b 1
)

echo ========================================
echo    Dynamic Pricing AI Web App
echo ========================================
echo.
echo Starting server (browser will NOT auto-open)...
echo You can manually open: http://localhost:8501
echo.

".venv\Scripts\python.exe" -m streamlit run app/streamlit_app.py --server.headless true --browser.gatherUsageStats false

echo.
echo App stopped. Press any key to exit...
pause >nul