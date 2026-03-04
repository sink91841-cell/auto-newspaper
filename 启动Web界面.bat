@echo off
chcp 65001 >nul
echo ================================================
echo 📰 自媒体报刊抓取工具 - Web界面启动器
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
pip list | findstr "flask" >nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Start the web interface launcher
echo Starting Web Interface...
echo ================================================
echo This will start the web server and open your browser
echo ================================================
python launch_web.py

echo ================================================
echo Web Interface stopped
echo Press any key to exit...
pause