@echo off
echo =================================
echo    Starting YouTube MP3 Bot
echo       (Multiuser Version)
echo =================================
echo.

REM Check if uv is installed
echo Checking uv installation...
uv --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv is not installed or not in PATH
    echo Please install uv first: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "bot_multiuser.py" (
    echo ERROR: bot_multiuser.py not found
    pause
    exit /b 1
)

if not exist ".env" (
    echo WARNING: .env file not found
    echo Make sure you have configured your TELEGRAM_BOT_TOKEN
    echo.
)

if not exist "pyproject.toml" (
    echo ERROR: pyproject.toml not found
    echo This is required for uv to work properly
    pause
    exit /b 1
)

REM Start the multiuser bot using uv
echo Starting multiuser bot with uv...
echo Press Ctrl+C to stop the bot
echo.

REM Use PowerShell to activate the environment and run the bot
powershell -Command "& { .\.venv\Scripts\Activate.ps1; python bot_multiuser.py }"

echo.
echo Bot stopped.
echo.
echo =================================
echo         Bot Stopped
echo =================================
pause
