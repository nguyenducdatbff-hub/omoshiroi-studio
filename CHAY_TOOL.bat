@echo off
cd /d "%~dp0"
title OMOSHIROI STUDIO - Trinh Tao Video TikTok Cham Biem
color 0E

echo =====================================================================
echo                OMOSHIROI STUDIO - SAN XUAT VIDEO SHORTS
echo =====================================================================
echo.
echo [*] Dang khoi dong he thong...

set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 set PYTHON_CMD=py

start "" powershell -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000'"

echo [*] Dang mo giao dien Web Studio tai dia chi: http://127.0.0.1:8000
echo [*] Trinh duyet web se tu dong mo len trong giay lat!
echo.
echo =====================================================================
echo  HUONG DAN SU DUNG:
echo  1. Trinh duyet web se tu dong bat len.
echo  2. Schon 1 trong 10 chu de drama ban muon lam.
echo  3. Tuy chinh cau thoai hoac bam "AI Viet Kich Ban" neu muon y tuong moi.
echo  4. Bam "XUAT BAN VIDEO" de may tu dong tao video va caption!
echo.
echo  (De tat tool, ban chi can dong cua so den nay lai la xong)
echo =====================================================================
echo.

%PYTHON_CMD% -m uvicorn web.app:app --host 127.0.0.1 --port 8000
if errorlevel 1 (
    echo.
    echo [LOI] Dang kiem tra va cai dat lai thu vien...
    %PYTHON_CMD% -m pip install -r requirements.txt
    %PYTHON_CMD% -m uvicorn web.app:app --host 127.0.0.1 --port 8000
)

pause
