@echo off
REM Test extraction logic with sample signals

echo ================================================
echo Testing Signal Extraction Logic
echo ================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+ or add it to PATH
    pause
    exit /b 1
)

echo Running extraction tests...
echo.

python tests\test_extraction.py

echo.
echo ================================================
echo Test complete!
echo ================================================
pause
