@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "MODE=%~1"
if "%MODE%"=="" set "MODE=webcam"

set "SERIAL_PORT=%~2"
set "SERIAL_BAUD=%~3"
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

if not "%SERIAL_PORT%"=="" (
    set "CONNECT4_ENABLE_SERIAL=1"
    set "CONNECT4_SERIAL_PORT=%SERIAL_PORT%"
    set "CONNECT4_SERIAL_BAUD=%SERIAL_BAUD%"
    echo Serial enabled on %CONNECT4_SERIAL_PORT% at %CONNECT4_SERIAL_BAUD% baud.
) else (
    set "CONNECT4_ENABLE_SERIAL="
    set "CONNECT4_SERIAL_PORT="
    set "CONNECT4_SERIAL_BAUD="
    echo Serial disabled. Pass a COM port as the second argument to enable it.
)

if /I "%MODE%"=="webcam" (
    %PYTHON_CMD% "%SCRIPT_DIR%connect4_webcam.py"
    goto :eof
)

if /I "%MODE%"=="terminal" (
    %PYTHON_CMD% "%SCRIPT_DIR%connect4_ai_test.py"
    goto :eof
)

if /I "%MODE%"=="ai" (
    %PYTHON_CMD% "%SCRIPT_DIR%connect4_ai_test.py"
    goto :eof
)

if /I "%MODE%"=="test" (
    %PYTHON_CMD% "%SCRIPT_DIR%connect4_ai_test.py"
    goto :eof
)

echo Unknown mode: %MODE%
echo Usage: run_connect4_windows.bat [webcam^|terminal] [COM_PORT] [BAUD]
exit /b 1
