@echo off
echo ========================================
echo   Starting Trading Bot
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the bot
python run_bot.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Bot stopped with error code: %errorlevel%
    pause
)
