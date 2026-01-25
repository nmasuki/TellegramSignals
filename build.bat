@echo off
echo ============================================================
echo Building Telegram Signal Extractor Portable Executable
echo ============================================================
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the build script
python scripts\build_exe.py

echo.
pause
