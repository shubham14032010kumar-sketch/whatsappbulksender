@echo off
title SHAKTIX — WhatsApp Bulk Campaign Suite v2.0 Commercial
cls
echo.
echo   ================================================================
echo   ███████ ██   ██  █████  ██   ██ ████████ ██ ██   ██
echo   ██      ██   ██ ██   ██ ██  ██     ██    ██  ██ ██
echo   ███████ ███████ ███████ █████      ██    ██   ███
echo        ██ ██   ██ ██   ██ ██  ██     ██    ██  ██ ██
echo   ███████ ██   ██ ██   ██ ██   ██    ██    ██ ██   ██
echo         Power Your Outreach.  ^|  v2.0 Commercial
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

echo [SHAKTIX] Launching Enterprise Application GUI...
%PYTHON_EXEC% app.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
