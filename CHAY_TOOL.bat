@echo off
chcp 65001 >nul
title OMOSHIROI STUDIO - Trình Tạo Video TikTok Châm Biếm
color 0E

echo =====================================================================
echo                OMOSHIROI STUDIO - SẢN XUẤT VIDEO SHORTS
echo =====================================================================
echo.
echo [*] Đang khởi động hệ thống...

:: Kiểm tra Python hoặc py launcher
set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=py
    ) else (
        color 0C
        echo [LỖI] Máy tính chưa nhận diện được Python.
        echo Hãy chạy file "CAI_DAT_NHANH.bat" trước nhé!
        echo.
        pause
        exit /b 1
    )
)

:: Tự động bật trình duyệt web sau 2 giây
start "" powershell -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8000'"

echo [*] Đang mở giao diện Web Studio tại địa chỉ: http://localhost:8000
echo [*] Trình duyệt web sẽ tự động mở lên trong giây lát!
echo.
echo =====================================================================
echo  HƯỚNG DẪN SỬ DỤNG:
echo  1. Trình duyệt web sẽ tự động bật lên.
echo  2. Chọn 1 trong 10 chủ đề drama bạn muốn làm.
echo  3. Tùy chỉnh câu thoại hoặc bấm "AI Viết Kịch Bản" nếu muốn ý tưởng mới.
echo  4. Bấm "XUẤT BẢN VIDEO" để máy tự động tạo video và caption!
echo.
echo  (Để tắt tool, bạn chỉ cần đóng cửa sổ đen này lại là xong)
echo =====================================================================
echo.

%PYTHON_CMD% -m uvicorn web.app:app --host 127.0.0.1 --port 8000
if %errorlevel% neq 0 (
    echo.
    echo [LỖI] Đang kiểm tra và cài đặt lại thư viện...
    %PYTHON_CMD% -m pip install -r requirements.txt
    %PYTHON_CMD% -m uvicorn web.app:app --host 127.0.0.1 --port 8000
)

pause
