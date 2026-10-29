@echo off
setlocal enabledelayedexpansion

:: =======================================================================
:: FairPool - One-Click Application Launcher
:: =======================================================================
title FairPool - Algorithmic Carpool Platform

:: Always ensure execution happens from the script directory
cd /d "%~dp0"

echo =======================================================================
echo               FAIRPOOL : ALGORITHMIC CARPOOL PLATFORM
echo =======================================================================
echo.

:: Detect Python executable
set "PYTHON_CMD="

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    echo [*] Using virtual environment (.venv)
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_CMD=venv\Scripts\python.exe"
    echo [*] Using virtual environment (venv)
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python"
    ) else (
        where py >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_CMD=py"
        )
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python was not found on your system!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Verify dependencies
echo [*] Checking dependencies...
"%PYTHON_CMD%" -c "import fastapi, uvicorn, numpy, scipy" >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] Missing dependencies detected. Installing required packages...
    "%PYTHON_CMD%" -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [OK] Dependencies successfully installed.
) else (
    echo [OK] All dependencies are ready.
)

echo.
echo =======================================================================
echo [*] Starting FairPool Web Application...
echo [*] Local URL: http://127.0.0.1:8000
echo [*] Opening application in your default web browser...
echo [*] To shut down the server, press Ctrl + C in this window.
echo =======================================================================
echo.

:: Automatically open default browser after a 2-second delay
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

:: Start the application server
"%PYTHON_CMD%" run.py --serve

:: If server stops, keep window open so the user can inspect output
if !errorlevel! neq 0 (
    echo.
    echo [!] FairPool server stopped with error code !errorlevel!.
) else (
    echo.
    echo [*] FairPool server has been stopped.
)

echo.
pause
