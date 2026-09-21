@echo off
chcp 65001 >nul
title Đẩy Cập Nhật Lên GitHub (Dành Cho Bạn)
color 0A

echo =====================================================================
echo         OMOSHIROI STUDIO - ĐẨY BẢN NÂNG CẤP LÊN GITHUB
echo =====================================================================
echo.

set /p COMMIT_MSG="Nhập nội dung cập nhật (hoặc ấn Enter để lấy mặc định): "
if "%COMMIT_MSG%"=="" (
    set COMMIT_MSG=Cap nhat tinh nang moi OMOSHIROI Studio
)

echo.
echo [1/3] Đang gom mã nguồn mới (Loại bỏ .env và output video)...
git add .

echo.
echo [2/3] Đang lưu thay đổi: "%COMMIT_MSG%"...
git commit -m "%COMMIT_MSG%"

echo.
echo [3/3] Đang đẩy lên GitHub nguyenducdatbff-hub/omoshiroi-studio...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo =====================================================================
    echo    🎉 ĐẨY LÊN GITHUB THÀNH CÔNG!
    echo    Bây giờ bên máy em bạn chỉ cần bấm "CAP_NHAT_TOOL.bat" là xong!
    echo =====================================================================
) else (
    echo.
    echo [LỖI] Đẩy lên GitHub không thành công. Hãy kiểm tra kết nối mạng.
)

echo.
pause
