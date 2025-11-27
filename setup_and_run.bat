@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "ROOT_DIR=%CD%"

echo ==========================================
echo      Lead Scrapper - Auto Setup And Run
echo ==========================================

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.13+.
    pause
    exit /b 1
)

REM Check for Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH. Please install Node.js v18+.
    pause
    exit /b 1
)

REM Check for uv
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 'uv' not found. Installing uv via pip...
    pip install uv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install uv. Please install it manually.
        pause
        exit /b 1
    )
)

echo.
echo [1/4] Setting up Backend...
cd "%ROOT_DIR%\backend"
if not exist .venv (
    echo Creating virtual environment...
)
call uv sync
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install backend dependencies.
    pause
    exit /b 1
)

echo Installing Playwright browsers...
call uv run playwright install
if %errorlevel% neq 0 (
    echo [WARNING] Playwright install had issues. You might need to run 'uv run playwright install' manually.
)

echo.
echo [2/4] Starting Backend Server...
echo Backend will run on http://localhost:8000 (API only)
start "Lead Scrapper Backend" cmd /k "uv run uvicorn app.main:app --reload"

echo.
echo [3/4] Setting up Frontend...
cd "%ROOT_DIR%\frontend"
if not exist node_modules (
    echo Installing frontend dependencies (this may take a while)...
    call npm install
) else (
    echo Node modules found. Skipping install.
)

echo.
echo [4/4] Starting Frontend Client...
echo The browser should open automatically when the frontend is ready...
start "Lead Scrapper Frontend" cmd /k "npm run dev"

echo.
echo ==========================================
echo      Setup Complete! App is running.
echo ==========================================
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo The browser should have opened automatically.
echo If not, we will force it open in 5 seconds...
timeout /t 5 >nul
start http://localhost:5173

echo.
echo Keep this window and the other two windows open.
pause
