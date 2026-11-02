@echo off
setlocal EnableExtensions
title GNSS Drift Atlas Editor

cd /d "%~dp0"

set "SERVER=%~dp0app\server.py"
set "URL=http://127.0.0.1:8765"
set "PYTHON="

if not exist "%SERVER%" (
    echo [ERROR] Cannot find the editor server:
    echo %SERVER%
    echo Make sure this file is inside the editor folder.
    pause
    exit /b 1
)

where py >nul 2>nul
if not errorlevel 1 set "PYTHON=py -3"

if not defined PYTHON (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON=python"
)

if not defined PYTHON (
    echo [ERROR] Python was not found.
    echo Install Python 3.10 or newer and enable the PATH option.
    pause
    exit /b 1
)

for /f "delims=" %%V in ('%PYTHON% -c "import sys; print(sys.version_info >= (3,10))" 2^>nul') do set "PY_OK=%%V"

if /i not "%PY_OK%"=="True" (
    echo [ERROR] Python 3.10 or newer is required.
    echo Detected interpreter: %PYTHON%
    pause
    exit /b 1
)

echo.
echo Starting GNSS Drift Atlas...
echo Editor URL: %URL%
echo Press Ctrl+C in this window to stop the server.
echo.

start "" powershell.exe -NoProfile -WindowStyle Hidden -Command "$limit=(Get-Date).AddSeconds(20); do { try { $client=[Net.Sockets.TcpClient]::new(); $client.Connect('127.0.0.1',8765); $client.Dispose(); Start-Process '%URL%'; exit 0 } catch { if ($client) { $client.Dispose() }; Start-Sleep -Milliseconds 300 } } while ((Get-Date) -lt $limit)"

%PYTHON% "%SERVER%"
set "SERVER_EXIT=%ERRORLEVEL%"

echo.
if not "%SERVER_EXIT%"=="0" (
    echo [ERROR] The editor server exited with code %SERVER_EXIT%.
) else (
    echo The editor server has stopped.
)
pause
exit /b %SERVER_EXIT%
