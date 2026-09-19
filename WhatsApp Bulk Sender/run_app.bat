@echo off
title WhatsApp Bulk Campaign Sender - Enterprise Edition
echo ===================================================
echo   WhatsApp Bulk Campaign Sender (V1 Commercial)
echo ===================================================
echo.
cd /d "%~dp0"
set PYTHON_EXEC=.venv\Scripts\python.exe

if not exist %PYTHON_EXEC% (
    if exist "C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\python.exe" (
        set PYTHON_EXEC="C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set PYTHON_EXEC="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else (
        set PYTHON_EXEC=python
    )
)

echo Launching Application...
%PYTHON_EXEC% app.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start. Make sure Python 3.8+ is installed.
    pause
)
