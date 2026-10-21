@echo off
title MedLab AI - Pan's Study Companion
color 0A
echo.
echo  ========================================
echo    MedLab AI - Pan's Study Companion
echo  ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python from https://python.org
    pause
    exit
)

:: Install dependencies if needed
echo  Checking dependencies...
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo  Installing required packages...
    pip install -r requirements.txt
    echo.
)

:: Check API key
findstr /C:"your_api_key_here" .env >nul 2>&1
if not errorlevel 1 (
    echo  [WARNING] Please add your Anthropic API key to the .env file first!
    echo  Open .env with Notepad and replace "your_api_key_here" with your key.
    echo.
    notepad .env
    pause
)

echo  Starting MedLab AI...
echo  Opening in your browser at http://localhost:8501
echo.
echo  To access from iPad: open http://YOUR-COMPUTER-IP:8501 on Safari
echo  (Find your IP: press Win+R, type cmd, then type "ipconfig")
echo.
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false
pause
