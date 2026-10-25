@echo off
title MuleShield AI Forensic Server
echo ========================================================
echo   Launching MuleShield AI Forensic Platform...
echo   URL: http://localhost:8001/dashboard
echo ========================================================
echo.

:: Automatically open the dashboard in your default browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8001/dashboard"

:: Start the MuleShield AI FastAPI server
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "run.py"
) else (
    python "run.py"
)

pause
