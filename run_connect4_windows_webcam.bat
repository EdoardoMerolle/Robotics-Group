@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "SERIAL_PORT=%~1"
if "%SERIAL_PORT%"=="" set "SERIAL_PORT=COM9"

set "SERIAL_BAUD=%~2"
if "%SERIAL_BAUD%"=="" set "SERIAL_BAUD=115200"

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
    ) else (
        set "PYTHON_CMD=python"
    )
)

set "CONNECT4_ENABLE_SERIAL=1"
set "CONNECT4_SERIAL_PORT=%SERIAL_PORT%"
set "CONNECT4_SERIAL_BAUD=%SERIAL_BAUD%"

echo Starting Connect 4 webcam mode...
echo Serial output to brain: %CONNECT4_SERIAL_PORT% at %CONNECT4_SERIAL_BAUD% baud.

%PYTHON_CMD% "%SCRIPT_DIR%connect4_webcam.py"
