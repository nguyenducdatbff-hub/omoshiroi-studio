@echo off
chcp 65001 >nul
title Cập Nhật OMOSHIROI STUDIO (1-Click)
color 0B

echo =====================================================================
echo           OMOSHIROI STUDIO - TỰ ĐỘNG CẬP NHẬT TÍNH NĂNG MỚI
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
        echo [LỖI] Không tìm thấy Python trên máy tính!
        echo Hãy mở file HUONG_DAN_CHO_EM.txt để xem cách cài Python.
        echo.
        pause
        exit /b 1
    )
)

:: 2. Chạy module updater
%PYTHON_CMD% core\updater.py

echo.
pause
