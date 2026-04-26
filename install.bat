@echo off
title OpenGuy Robotics — Installer
color 0A
echo.
echo  ============================================
echo    OpenGuy Robotics — Smart Auto-Installer
echo  ============================================
echo.

:: ── Step 1: Check if Python 3.10-3.13 is available ──
set PYTHON_CMD=
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
    echo [INFO] Found Python !PYVER!
)

setlocal enabledelayedexpansion

:: Try python, python3, py launcher
for %%P in (python python3 py) do (
    where %%P >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        for /f "tokens=2 delims= " %%v in ('%%P --version 2^>^&1') do (
            set FULL_VER=%%v
            for /f "tokens=1,2 delims=." %%a in ("%%v") do (
                set MAJOR=%%a
                set MINOR=%%b
            )
        )
        if !MAJOR! equ 3 (
            if !MINOR! geq 10 if !MINOR! leq 13 (
                set PYTHON_CMD=%%P
                echo [OK] Compatible Python found: %%P ^(!FULL_VER!^)
                goto :python_ready
            )
        )
    )
)

:: No compatible Python found — install via winget
echo.
echo [WARN] No compatible Python 3.10-3.13 found on this system.
echo [INFO] Attempting to install Python 3.12 via winget...
echo.

where winget >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] winget is not available on this system.
    echo.
    echo  Please install Python 3.12 manually from:
    echo  https://www.python.org/downloads/release/python-3129/
    echo.
    echo  IMPORTANT: Check "Add python.exe to PATH" during install!
    echo.
    pause
    exit /b 1
)

winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python installation failed.
    echo  Please install Python 3.12 manually from:
    echo  https://www.python.org/downloads/release/python-3129/
    pause
    exit /b 1
)

:: Refresh PATH so we can find the newly installed Python
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312\;%LOCALAPPDATA%\Programs\Python\Python312\Scripts\;%PATH%"
set PYTHON_CMD=python
echo [OK] Python 3.12 installed successfully.

:python_ready
echo.

:: ── Step 2: Check if Git is available ──
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] Git not found. Attempting to install via winget...
    where winget >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] winget not available. Please install Git from https://git-scm.com/downloads
        pause
        exit /b 1
    )
    winget install Git.Git --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Git installation failed. Please install from https://git-scm.com/downloads
        pause
        exit /b 1
    )
    :: Refresh PATH
    set "PATH=C:\Program Files\Git\cmd;%PATH%"
    echo [OK] Git installed successfully.
)

echo.

:: ── Step 3: Clone the repository ──
if exist OpenGuy (
    echo [INFO] OpenGuy directory already exists. Pulling latest changes...
    cd OpenGuy
    git pull
) else (
    echo [INFO] Cloning OpenGuy repository...
    git clone https://github.com/OPENEHIRA/OpenGuy.git
    cd OpenGuy
)

echo.

:: ── Step 4: Install Python dependencies ──
echo [INFO] Installing dependencies...
%PYTHON_CMD% -m pip install --upgrade pip >nul 2>&1
%PYTHON_CMD% -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Dependency installation failed.
    echo  Try running: %PYTHON_CMD% -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo  ============================================
echo    All dependencies installed successfully!
echo  ============================================
echo.
echo  Starting OpenGuy server on http://localhost:5000
echo  Press Ctrl+C to stop the server.
echo.

:: ── Step 5: Start the server ──
%PYTHON_CMD% server.py

pause
