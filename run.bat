@echo off
REM Telegram Signal Extractor - Quick Start Script

echo ================================================
echo Telegram Signal Extractor
echo ================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found.
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo.
    echo ERROR: .env file not found!
    echo Please copy config\.env.example to .env and configure your credentials.
    echo.
    pause
    exit /b 1
)

REM Run the application
echo Starting Telegram Signal Extractor...
echo.
python src\main.py

REM Deactivate on exit
deactivate

pause
