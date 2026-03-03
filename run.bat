@echo off
chcp 65001 >nul
echo ================================================
echo 自媒体报刊抓取工具
echo ================================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python 3.8 or higher
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check dependencies
echo Checking dependencies...
pip list | findstr "requests" >nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check .env file
if not exist .env (
    echo WARNING: .env file not found
    echo Creating default .env file...
    copy .env.example .env >nul
    if errorlevel 1 (
        echo ERROR: Failed to create .env file
        pause
        exit /b 1
    )
    echo Default .env file created successfully
    echo Please edit .env file to configure API Key and database settings
    pause
)

REM Run the program
echo Starting newspaper tool...
echo ================================================
python main.py

REM Check exit status
if errorlevel 1 (
    echo Program failed
    pause
    exit /b 1
)

echo ================================================
echo Program completed
echo Press any key to exit...
pause