@echo off
setlocal enabledelayedexpansion

:: Enhanced Full Stack Launcher with Advanced Features
:: Version 3.0 - Production Ready

:: Configuration
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"
set "MAX_WAIT_TIME=30"
set "HEALTH_CHECK_INTERVAL=2"
set "LOG_FILE=app_launcher.log"
set "CONFIG_FILE=launcher_config.ini"

:: Set window title
title Dynamic Pricing AI Launcher v3.0

:: Initialize logging
echo [%date% %time%] Starting launcher > "%LOG_FILE%"

:: Load configuration if exists
if exist "%CONFIG_FILE%" (
    for /f "tokens=1,2 delims==" %%a in ('type "%CONFIG_FILE%" ^| findstr "="') do (
        set "%%a=%%b"
    )
    echo [INFO] Configuration loaded from %CONFIG_FILE%
)

cls
echo.
echo ================================================
echo   Dynamic Pricing AI - Full Stack Launcher v3.0
echo ================================================
echo.

:: Change to project directory
cd /d "%~dp0" 2>nul
if errorlevel 1 (
    echo [ERROR] Cannot change to project directory
    goto :errorExit
)

:: Check prerequisites
echo [%date% %time%] INFO: Starting checkPrerequisites >> "%LOG_FILE%"
call :checkPrerequisites
if errorlevel 1 (
    echo [%date% %time%] ERROR: checkPrerequisites failed >> "%LOG_FILE%"
    goto :errorExit
)
echo [%date% %time%] INFO: Completed checkPrerequisites >> "%LOG_FILE%"

:: Clean up existing processes (run before port checks)
echo [%date% %time%] INFO: Starting cleanupProcesses >> "%LOG_FILE%"
call :cleanupProcesses
if errorlevel 1 (
    echo [%date% %time%] ERROR: cleanupProcesses failed >> "%LOG_FILE%"
    goto :errorExit
)
echo [%date% %time%] INFO: Completed cleanupProcesses >> "%LOG_FILE%"

:: Validate port availability
echo [%date% %time%] INFO: Starting validatePorts >> "%LOG_FILE%"
call :validatePorts
if errorlevel 1 (
    echo [%date% %time%] ERROR: validatePorts failed >> "%LOG_FILE%"
    goto :errorExit
)
echo [%date% %time%] INFO: Completed validatePorts >> "%LOG_FILE%"

:: Check and install dependencies
echo Checking dependencies...
echo [%date% %time%] INFO: Starting checkDependencies >> "%LOG_FILE%"
call :checkDependencies
if errorlevel 1 (
    echo [%date% %time%] ERROR: checkDependencies failed >> "%LOG_FILE%"
    goto :errorExit
)
echo [%date% %time%] INFO: Completed checkDependencies >> "%LOG_FILE%"

:: Start servers with monitoring
echo [%date% %time%] INFO: Starting startServers >> "%LOG_FILE%"
call :startServers
if errorlevel 1 (
    echo [%date% %time%] ERROR: startServers failed >> "%LOG_FILE%"
    goto :errorExit
)
echo [%date% %time%] INFO: Completed startServers >> "%LOG_FILE%"

:: Show final status and instructions
echo [%date% %time%] INFO: Calling showFinalStatus >> "%LOG_FILE%"
call :showFinalStatus
echo [%date% %time%] INFO: Completed showFinalStatus >> "%LOG_FILE%"


goto :normalExit

:: ============================================
:: Function Definitions
:: ============================================

:initLogging
echo [%date% %time%] Starting launcher > "%LOG_FILE%"
goto :eof

:loadConfig
if exist "%CONFIG_FILE%" (
    for /f "tokens=1,2 delims==" %%a in ('type "%CONFIG_FILE%" ^| findstr "="') do (
        set "%%a=%%b"
    )
    echo [INFO] Configuration loaded from %CONFIG_FILE%
)
goto :eof

:saveConfig
(
    echo BACKEND_PORT=%BACKEND_PORT%
    echo FRONTEND_PORT=%FRONTEND_PORT%
    echo MAX_WAIT_TIME=%MAX_WAIT_TIME%
) > "%CONFIG_FILE%"
goto :eof

:checkAdminPrivileges
net session >nul 2>&1
if errorlevel 1 (
    exit /b 1
) else (
    echo [OK] Running with admin privileges
    exit /b 0
)
goto :eof

:checkPrerequisites
echo Checking prerequisites...

:: Check Python
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found in PATH
        echo Please install Python 3.8+ and add it to PATH
        echo [%date% %time%] ERROR: Python not found >> "%LOG_FILE%"
        exit /b 1
    )
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%v"
    echo [OK] Python %PYTHON_VERSION% found
    echo [%date% %time%] INFO: Python %PYTHON_VERSION% available >> "%LOG_FILE%"


:: Check Node.js
    node --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Node.js not found in PATH
        echo Please install Node.js 16+ and add it to PATH
        echo [%date% %time%] ERROR: Node.js not found >> "%LOG_FILE%"
        exit /b 1
    )
    for /f "tokens=*" %%v in ('node --version 2^>^&1') do set "NODE_VERSION=%%v"
    echo [OK] Node.js %NODE_VERSION% found
    echo [%date% %time%] INFO: Node.js %NODE_VERSION% available >> "%LOG_FILE%"


:: Check Git (optional but recommended)
    git --version >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Git not found - version control features disabled
        echo [%date% %time%] WARN: Git not found >> "%LOG_FILE%"
    ) else (
        for /f "tokens=3" %%v in ('git --version 2^>^&1') do set "GIT_VERSION=%%v"
        echo [OK] Git %GIT_VERSION% found
        echo [%date% %time%] INFO: Git %GIT_VERSION% available >> "%LOG_FILE%"
    )


echo.
goto :eof

:validatePorts
echo Validating port availability...
echo [%date% %time%] INFO: validatePorts started >> "%LOG_FILE%"

set "FOUND="
:: Check backend port using for/f to reliably capture presence
set "FOUND="
for /f "delims=" %%L in ('netstat -an ^| find ":%BACKEND_PORT%" ^| find "LISTENING" 2^>nul') do set "FOUND=1"
if defined FOUND (
    echo [ERROR] Port %BACKEND_PORT% is already in use
    echo [%date% %time%] ERROR: Port %BACKEND_PORT% in use >> "%LOG_FILE%"
    echo [%date% %time%] INFO: Listing processes using port %BACKEND_PORT% >> "%LOG_FILE%"
    netstat -ano | find ":%BACKEND_PORT%" >> "%LOG_FILE%" 2>&1
    exit /b 1
)
echo [OK] Backend port %BACKEND_PORT% available
echo [%date% %time%] INFO: Backend port %BACKEND_PORT% available >> "%LOG_FILE%"

set "FOUND="
:: Check frontend port using for/f to reliably capture presence
set "FOUND="
for /f "delims=" %%L in ('netstat -an ^| find ":%FRONTEND_PORT%" ^| find "LISTENING" 2^>nul') do set "FOUND=1"
if defined FOUND (
    echo [ERROR] Port %FRONTEND_PORT% is already in use
    echo [%date% %time%] ERROR: Port %FRONTEND_PORT% in use >> "%LOG_FILE%"
    echo [%date% %time%] INFO: Listing processes using port %FRONTEND_PORT% >> "%LOG_FILE%"
    netstat -ano | find ":%FRONTEND_PORT%" >> "%LOG_FILE%" 2>&1
    exit /b 1
)
echo [OK] Frontend port %FRONTEND_PORT% available
echo [%date% %time%] INFO: Frontend port %FRONTEND_PORT% available >> "%LOG_FILE%"

echo.
echo [%date% %time%] INFO: validatePorts completed >> "%LOG_FILE%"
goto :eof



:cleanupProcesses
echo Cleaning up existing processes...
echo [%date% %time%] INFO: Starting cleanupProcesses >> "%LOG_FILE%"
:: Enhanced cleanup with better error handling
taskkill /F /T /FI "WINDOWTITLE eq Backend API*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq Frontend Dev*" >nul 2>&1

:: Use netstat to find and kill processes listening on the configured ports
echo [%date% %time%] INFO: Detecting processes using ports %BACKEND_PORT% and %FRONTEND_PORT% >> "%LOG_FILE%"
for /f "tokens=5" %%p in ('netstat -ano ^| find ":%BACKEND_PORT%" ^| find "LISTENING" 2^>nul') do (
    echo [%date% %time%] INFO: Found process %%p listening on port %BACKEND_PORT% >> "%LOG_FILE%"
    taskkill /F /PID %%p >nul 2>&1 || echo [%date% %time%] WARN: Failed to kill PID %%p >> "%LOG_FILE%"
)
for /f "tokens=5" %%p in ('netstat -ano ^| find ":%FRONTEND_PORT%" ^| find "LISTENING" 2^>nul') do (
    echo [%date% %time%] INFO: Found process %%p listening on port %FRONTEND_PORT% >> "%LOG_FILE%"
    taskkill /F /PID %%p >nul 2>&1 || echo [%date% %time%] WARN: Failed to kill PID %%p >> "%LOG_FILE%"
)
:: Fallback: kill common process names
for /f "tokens=2" %%a in ('wmic process where "name='uvicorn.exe'" get processid /format:value 2^>nul ^| findstr "ProcessId"') do (
    echo [%date% %time%] INFO: Killing uvicorn pid %%a >> "%LOG_FILE%"
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=2" %%a in ('wmic process where "name='node.exe'" get processid /format:value 2^>nul ^| findstr "ProcessId"') do (
    echo [%date% %time%] INFO: Killing node pid %%a >> "%LOG_FILE%"
    taskkill /F /PID %%a >nul 2>&1
)

ping 127.0.0.1 -n 2 >nul
echo [%date% %time%] INFO: Cleanup complete >> "%LOG_FILE%"
echo.
goto :eof


:checkDependencies
echo Checking dependencies...

:: Python dependencies - simplified check
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing Python packages...
    echo [%date% %time%] INFO: Installing Python packages >> "%LOG_FILE%"
    pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install Python packages
        echo [%date% %time%] ERROR: Python package installation failed >> "%LOG_FILE%"
        exit /b 1
    )
    echo [OK] Python packages installed
    echo [%date% %time%] INFO: Python packages installed >> "%LOG_FILE%"
) else (
    echo [OK] Python packages ready
    echo [%date% %time%] INFO: Python packages present >> "%LOG_FILE%"
)


:: Node.js dependencies
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    echo [%date% %time%] INFO: Installing frontend dependencies >> "%LOG_FILE%"
    cd frontend
    call npm install >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        cd ..
        echo [ERROR] Failed to install frontend dependencies
        echo [%date% %time%] ERROR: Frontend dependency installation failed >> "%LOG_FILE%"
        exit /b 1
    )
    cd ..
    echo [OK] Frontend dependencies installed
    echo [%date% %time%] INFO: Frontend dependencies installed >> "%LOG_FILE%"
) else (
    echo [OK] Frontend dependencies ready
    echo [%date% %time%] INFO: Frontend dependencies present >> "%LOG_FILE%"
)


echo.
goto :eof

:startServers
echo Starting servers...

:: Start Backend with enhanced monitoring
echo Starting Backend API (port %BACKEND_PORT%)...
echo [%date% %time%] INFO: Starting Backend process >> "%LOG_FILE%"
start "Backend API" cmd /c "title Backend API && python -m uvicorn backend.main:app --reload --port %BACKEND_PORT% --host 127.0.0.1" >nul 2>&1

:: Wait for backend with progress indicator
call :waitForService "Backend" %BACKEND_PORT%
if errorlevel 1 (
    echo [ERROR] Backend failed to start properly
    echo [%date% %time%] ERROR: Backend startup failed >> "%LOG_FILE%"
    exit /b 1
)

echo [%date% %time%] INFO: Backend reported listening on port %BACKEND_PORT% >> "%LOG_FILE%"
ping 127.0.0.1 -n 2 >nul

:: Start Frontend with enhanced monitoring
echo Starting Frontend Dev Server (port %FRONTEND_PORT%)...
echo [%date% %time%] INFO: Starting Frontend process >> "%LOG_FILE%"
start "Frontend Dev" cmd /c "title Frontend Dev && cd frontend && npm run dev" >nul 2>&1

:: Wait for frontend with progress indicator
call :waitForService "Frontend" %FRONTEND_PORT%
if errorlevel 1 (
    echo [WARNING] Frontend may not have started properly
    echo [%date% %time%] WARNING: Frontend startup issues >> "%LOG_FILE%"
)

echo [%date% %time%] INFO: startServers finished >> "%LOG_FILE%"
echo.
goto :eof


:waitForService
set "service_name=%~1"
set "port=%~2"
set "attempts=0"

:wait_loop
set /a attempts+=1
netstat -an | find ":%port%" | find "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [OK] %service_name% started successfully (attempt !attempts!)
    echo [%date% %time%] INFO: %service_name% started on port %port% >> "%LOG_FILE%"
    exit /b 0
)

if !attempts! geq %MAX_WAIT_TIME% (
    echo [ERROR] %service_name% failed to start within %MAX_WAIT_TIME% seconds
    echo [%date% %time%] ERROR: %service_name% timeout on port %port% >> "%LOG_FILE%"
    exit /b 1
)

echo Waiting for %service_name%... !attempts!/%MAX_WAIT_TIME% seconds
ping 127.0.0.1 -n %HEALTH_CHECK_INTERVAL% >nul
goto :wait_loop

:showFinalStatus
echo ================================================
echo   SERVERS STARTED!
echo ================================================
echo.
echo   Frontend: http://localhost:%FRONTEND_PORT%
echo   Backend:  http://127.0.0.1:%BACKEND_PORT%
echo   API Docs: http://127.0.0.1:%BACKEND_PORT%/docs
echo.
echo ================================================

:: Enhanced status display
echo Current server status:
call :checkServiceStatus "Backend API" %BACKEND_PORT%
call :checkServiceStatus "Frontend Dev" %FRONTEND_PORT%

echo.
echo Control Options:
echo   1. Close "Backend API" and "Frontend Dev" windows to stop servers
echo   2. Run this script again to cleanup and restart
echo   3. Check %LOG_FILE% for detailed logs
echo   4. Use Ctrl+C in server windows for graceful shutdown
echo.

:: Save current configuration
(
    echo BACKEND_PORT=%BACKEND_PORT%
    echo FRONTEND_PORT=%FRONTEND_PORT%
    echo MAX_WAIT_TIME=%MAX_WAIT_TIME%
) > "%CONFIG_FILE%"

echo [%date% %time%] INFO: All services started successfully >> "%LOG_FILE%"
goto :eof

:checkServiceStatus
set "service_name=%~1"
set "port=%~2"

echo %service_name% Port %port%:
set "FOUND="
for /f "delims=" %%L in ('netstat -an ^| find ":%port%" ^| find "LISTENING" 2^>nul') do set "FOUND=1"
if defined FOUND (
    echo   [OK] Running
    echo [%date% %time%] INFO: %service_name% running on port %port% >> "%LOG_FILE%"
) else (
    echo   [ERROR] Not running
    echo [%date% %time%] WARN: %service_name% not running on port %port% >> "%LOG_FILE%"
)
 goto :eof


:errorExit
echo.
echo ================================================
echo   FATAL ERROR - Launcher stopped
echo ================================================
echo Check %LOG_FILE% for error details
echo.
echo [%date% %time%] ERROR: Exiting with errorlevel %errorlevel% >> "%LOG_FILE%"
if defined NONINTERACTIVE (
    echo NONINTERACTIVE set, not pausing
) else (
    pause
)
exit /b 1


:normalExit
echo.
echo Launcher completed successfully
echo [%date% %time%] INFO: Launcher completed normally >> "%LOG_FILE%"
pause
exit /b 0