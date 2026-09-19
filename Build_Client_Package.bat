@echo off
title Build Commercial Client Edition Package
echo =========================================================
echo   WhatsApp Bulk Campaign Sender — Commercial Packager
echo   Building clean Client Edition without Super Admin
echo =========================================================
echo.
cd /d "%~dp0WhatsApp Bulk Sender"
set PYTHON_EXEC=.venv\Scripts\python.exe

if not exist %PYTHON_EXEC% (
    set PYTHON_EXEC=python
)

%PYTHON_EXEC% package_client_edition.py

echo.
echo Client zip file is ready inside the "dist\" folder.
echo You can send this zip directly to buyers!
echo.
pause
