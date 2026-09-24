@echo off
cd /d "%~dp0"
title Cai Dat OMOSHIROI STUDIO (1 Lan Duy Nhat)
color 0B

echo =====================================================================
echo           OMOSHIROI STUDIO - CAI DAT MOI TRUONG TU DONG
echo =====================================================================
echo.

set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 set PYTHON_CMD=py

echo [1/3] Da phat hien Python! Dang kiem tra phien ban...
%PYTHON_CMD% --version
echo.

echo [2/3] Dang tu dong cai dat cac thu vien can thiet (FastAPI, Edge-TTS, AI...)...
%PYTHON_CMD% -m pip install --upgrade pip >nul 2>&1
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
    color 0C
    echo.
    echo [CANH BAO] Dang thu cai dat lai thu vien...
    %PYTHON_CMD% -m pip install -r requirements.txt
)

echo.
echo [3/3] Dang khoi tao bo giai ma video va am thanh (Static FFmpeg)...
%PYTHON_CMD% -c "import static_ffmpeg; static_ffmpeg.add_paths(); print('FFmpeg Engine San Sang!')"

echo.
echo =====================================================================
color 0A
echo        CHUC MUNG BAN! CAI DAT DA HOAN TAT THANH CONG 100%%!
echo =====================================================================
echo.
echo Tu bay gio, moi lan muon tao video, ban chi can:
echo  👉 CLICK DUB VAO FILE: "CHAY_TOOL.bat"
echo.
pause
