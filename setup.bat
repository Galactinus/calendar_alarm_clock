@echo off

REM Check if Python 3 is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python 3 is not installed. Please install Python 3 first.
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

echo Setup complete! To activate the virtual environment, run:
echo venv\Scripts\activate.bat

pause 