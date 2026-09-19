@echo off
title SHAKTIX — WhatsApp Campaign Suite v2.0 Commercial [DEMO MODE]
cls
echo.
echo   ================================================================
echo   ███████ ██   ██  █████  ██   ██ ████████ ██ ██   ██
echo   ██      ██   ██ ██   ██ ██  ██     ██    ██  ██ ██
echo   ███████ ███████ ███████ █████      ██    ██   ███
echo        ██ ██   ██ ██   ██ ██  ██     ██    ██  ██ ██
echo   ███████ ██   ██ ██   ██ ██   ██    ██    ██ ██   ██
echo         Power Your Outreach.  ^|  v2.0 Commercial [DEMO]
echo   ================================================================
echo.

cd /d "%~dp0"
set PYTHON_EXEC=.venv\Scripts\python.exe

if not exist %PYTHON_EXEC% (
    if exist "C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe" (
        set PYTHON_EXEC="C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe"
    ) else (
        set PYTHON_EXEC=python
    )
)

echo [SHAKTIX] Initializing 250 Demo Leads ^& 12 Client Demo Campaigns...
%PYTHON_EXEC% demo\demo_seed.py

echo.
echo [SHAKTIX] Launching Application in Demo Mode...
%PYTHON_EXEC% app.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
