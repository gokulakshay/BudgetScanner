@echo off
REM Budget Dashboard launcher script

SETLOCAL

REM Determine script directory
SET "SCRIPT_DIR=%~dp0"

REM Check for virtual environment
SET "VENV_DIR=%SCRIPT_DIR%venv"
IF EXIST "%VENV_DIR%" (
    REM Activate virtual environment
    CALL "%VENV_DIR%\Scripts\activate.bat"
) ELSE (
    ECHO Virtual environment not found at %VENV_DIR%
    ECHO Running setup first...
    python "%SCRIPT_DIR%setup.py"
    CALL "%VENV_DIR%\Scripts\activate.bat"
)

REM Launch the dashboard
python "%SCRIPT_DIR%run_dashboard.py" %*

ENDLOCAL