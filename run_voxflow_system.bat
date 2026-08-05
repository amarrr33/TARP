@echo off
echo ========================================================
echo        Starting VoxFlow Host Software Suite
echo ========================================================
echo.
echo 1. Starting Flask REST Server (http://localhost:5000)...
start "VoxFlow Flask REST Server" cmd /k "python server.py"

timeout /t 2 /nobreak >nul

echo 2. Launching Streamlit Live Dashboard (http://localhost:8501)...
start "VoxFlow Analytics Dashboard" cmd /k "streamlit run dashboard.py"

echo.
echo VoxFlow system is now active!
echo - Flask REST API: http://localhost:5000
echo - Live Dashboard:  http://localhost:8501
echo.
pause
