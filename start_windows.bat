@echo off
REM Chaos Foundry Unified Publishing Service - Windows Launcher
echo Starting Unified Publisher...

REM Check if venv exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Run the application
echo Launching Unified Publisher...
python -m publisherlogic.main

pause
