@echo off
REM Netcat Quick Start Script for Windows
REM Installs the locked dependencies (uv.lock) with uv and starts the application.

cd /d "%~dp0"

echo.
echo ========================================
echo        Netcat - Network Utility
echo ========================================
echo.

REM uv installs the right Python version and the exact versions from uv.lock
where uv >nul 2>&1
if errorlevel 1 (
    echo Error: uv is not installed or not in PATH
    echo See https://docs.astral.sh/uv/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('uv --version') do set UV_VERSION=%%i
echo + %UV_VERSION% found
echo.

echo Installing dependencies from uv.lock...
uv sync --frozen --no-dev
if errorlevel 1 (
    echo Error: could not install dependencies
    pause
    exit /b 1
)
echo + Dependencies installed

echo.
echo ========================================
echo       Starting Netcat Application
echo ========================================
echo.
echo Access the application at: http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the application
uv run --frozen --no-dev python app.py

pause
