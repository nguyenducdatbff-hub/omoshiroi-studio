@echo off
cd /d "%~dp0"
title Cap Nhat OMOSHIROI STUDIO (1-Click)
color 0B

echo =====================================================================
echo           OMOSHIROI STUDIO - TU DONG CAP NHAT TINH NANG MOI
echo =====================================================================
echo.

set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 set PYTHON_CMD=py

%PYTHON_CMD% core\updater.py

echo.
pause
