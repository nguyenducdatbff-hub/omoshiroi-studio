@echo off
chcp 65001 >nul
title Cài Đặt OMOSHIROI STUDIO (1 Lần Duy Nhất)
color 0B

echo =====================================================================
echo           OMOSHIROI STUDIO - CÀI ĐẶT MÔI TRƯỜNG TỰ ĐỘNG
echo =====================================================================
echo.

:: 1. Kiểm tra Python hoặc Py
set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=py
    ) else (
        color 0C
        echo [LỖI] Máy tính của bạn chưa nhận diện được Python!
        echo.
        echo Hãy thử khởi động lại máy tính hoặc mở lại cửa sổ này nhé.
        echo.
        pause
        exit /b 1
    )
)

echo [1/3] Đã phát hiện Python! Đang kiểm tra phiên bản...
%PYTHON_CMD% --version
echo.

echo [2/3] Đang tự động cài đặt các thư viện cần thiết (FastAPI, Edge-TTS, AI...)...
%PYTHON_CMD% -m pip install --upgrade pip >nul 2>&1
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [CẢNH BÁO] Đang thử cài đặt lại thư viện...
    %PYTHON_CMD% -m pip install -r requirements.txt
)

echo.
echo [3/3] Đang khởi tạo bộ giải mã video và âm thanh (Static FFmpeg)...
%PYTHON_CMD% -c "import static_ffmpeg; static_ffmpeg.add_paths(); print('FFmpeg Engine Sẵn Sàng!')"

echo.
echo =====================================================================
color 0A
echo        CHÚC MỪNG BẠN! CÀI ĐẶT ĐÃ HOÀN TẤT THÀNH CÔNG 100%%!
echo =====================================================================
echo.
echo Từ bây giờ, mỗi lần muốn tạo video, bạn chỉ cần:
echo  👉 CLICK ĐÚP VÀO FILE: "CHAY_TOOL.bat"
echo.
pause
