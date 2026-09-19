@echo off
title Connect WhatsApp Bulk Sender to GitHub
echo ========================================================
echo   ShaktiX WhatsApp Bulk Sender — GitHub Setup Wizard
echo ========================================================
echo.

cd /d "%~dp0"

where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [NOTICE] Git command line was not found on your system PATH.
    echo.
    echo Would you like to automatically install Git now via Windows winget?
    set /p INSTALL_GIT="Install Git automatically? (Y/N): "
    if /i "%INSTALL_GIT%"=="Y" (
        echo.
        echo Installing Git via winget...
        winget install --id Git.Git -e --source winget
        echo.
        echo Git installation completed. Please close and re-open this script.
        pause
        exit /b
    ) else (
        echo.
        echo Please install Git manually from https://git-scm.com/downloads and run this script again.
        pause
        exit /b
    )
)

echo [OK] Git is installed and available!
echo.

if not exist ".git" (
    echo Initializing local Git repository...
    git init -b main
) else (
    echo Local Git repository already initialized.
)

echo.
echo Staging project files (excluding virtualenvs, backups and chrome sessions)...
git add .gitignore
git add README.md
git add Launch_WhatsApp_Bulk_Sender.bat
git add Generate_License_Key.bat
git add Build_Client_Package.bat
git add web_portal/
git add "WhatsApp Bulk Sender/app.py"
git add "WhatsApp Bulk Sender/core/"
git add "WhatsApp Bulk Sender/ui/"
git add "WhatsApp Bulk Sender/api/"
git add "WhatsApp Bulk Sender/package_client_edition.py"
git add "WhatsApp Bulk Sender/requirements.txt"
git add "WhatsApp Bulk Sender/run_app.bat"
git add "WhatsApp Bulk Sender/license_generator.py"
git add "WhatsApp Bulk Sender/test_*.py"

echo.
git commit -m "ShaktiX WhatsApp Bulk Sender Enterprise v2.5 with AI Spintax, Lead Extractor and Client Packaging"

echo.
echo ========================================================
echo   Local commit successful!
echo ========================================================
echo.
echo Now, create a new empty repository on your GitHub account:
echo 1. Go to: https://github.com/new
echo 2. Repository name: whatsapp-bulk-sender
echo 3. Keep it Private (or Public if you wish)
echo 4. Click 'Create repository'
echo.
set /p REPO_URL="Enter your GitHub Repository URL (e.g. https://github.com/yourname/repo.git): "

if "%REPO_URL%"=="" (
    echo No repository URL entered. Your local changes are committed safely.
    pause
    exit /b
)

git remote remove origin >nul 2>nul
git remote add origin %REPO_URL%
echo.
echo Pushing code to GitHub...
git push -u origin main

echo.
echo ========================================================
echo   All Done! Code is now live and synced on GitHub!
echo ========================================================
pause
