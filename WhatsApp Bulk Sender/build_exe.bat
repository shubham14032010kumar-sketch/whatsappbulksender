@echo off
title Enterprise WhatsApp Bulk Sender - Executable Builder
echo ================================================================
echo Building Standalone Windows Executable (.exe)
echo No Python installation required for end-customers!
echo ================================================================
echo.

cd /d "%~dp0"
set PYTHON_CMD=.venv\Scripts\python.exe
if not exist %PYTHON_CMD% (
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else (
        set PYTHON_CMD=python
    )
)

echo [1/3] Checking PyInstaller...
%PYTHON_CMD% -m pip install pyinstaller --quiet

echo [2/3] Compiling WhatsAppBulkSender.exe with PyInstaller...
%PYTHON_CMD% -m PyInstaller --noconfirm --onedir --windowed ^
    --name "WhatsAppBulkSender" ^
    --add-data "ui;ui" ^
    --add-data "core;core" ^
    --add-data "api;api" ^
    --hidden-import "sqlite3" ^
    --hidden-import "openpyxl" ^
    --hidden-import "pandas" ^
    app.py

echo.
echo ================================================================
if %errorlevel% equ 0 (
    echo BUILD SUCCESS! Standalone folder created at: dist\WhatsAppBulkSender\
    echo You can distribute this folder or zip it for fresh Windows machines.
) else (
    echo Build encountered an issue. Ensure Python and pip are installed.
)
echo ================================================================
pause
