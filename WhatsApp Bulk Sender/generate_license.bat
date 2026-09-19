@echo off
title WhatsApp Bulk Sender - License Generator (Admin Tool)
echo ========================================================
echo   WhatsApp Bulk Sender - Commercial License Generator
echo ========================================================
echo.
cd /d "%~dp0"
set PYTHON_EXEC=.venv\Scripts\python.exe
if not exist %PYTHON_EXEC% set PYTHON_EXEC=python

echo Launching License Key Generator GUI...
%PYTHON_EXEC% license_generator.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Make sure Python is installed and in PATH.
    pause
)
