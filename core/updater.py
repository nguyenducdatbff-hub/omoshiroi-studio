"""
OMOSHIROI Studio - Auto Updater
Tự động cập nhật mã nguồn từ GitHub nguyenducdatbff-hub/omoshiroi-studio
Hoàn toàn không ghi đè .env (API key) hoặc thư mục output/ (video đã tạo).
"""

import os
import sys
import shutil
import urllib.request
import zipfile
import subprocess
from pathlib import Path

# Đảm bảo in tiếng Việt mượt mà trên mọi máy tính Windows mà không bị lỗi mã ký tự Unicode
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

GITHUB_REPO_ZIP = "https://github.com/nguyenducdatbff-hub/omoshiroi-studio/archive/refs/heads/main.zip"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Các thư mục / file TUYỆT ĐỐI KHÔNG ĐƯỢC GHI ĐÈ hoặc XÓA
PROTECTED_PATHS = {
    ".env",
    "output",
    ".venv",
    "venv",
    "temp_scratch",
}

# Các thư mục / file mã nguồn cần cập nhật
UPDATE_TARGETS = [
    "core",
    "web",
    "assets",
    "requirements.txt",
    "README.md",
    "CAI_DAT_NHANH.bat",
    "CHAY_TOOL.bat",
    "CAP_NHAT_TOOL.bat",
    "HUONG_DAN_CHO_EM.txt",
    ".env.example",
]

def print_banner():
    print("=" * 65)
    print("           OMOSHIROI STUDIO - BỘ CẬP NHẬT TỰ ĐỘNG (1-CLICK)")
    print("=" * 65)
    print()

def download_and_update():
    print_banner()
    temp_zip = PROJECT_ROOT / "temp_update.zip"
    temp_extract = PROJECT_ROOT / "temp_update_extracted"

    try:
        print("[1/4] Đang kết nối tới GitHub và tải bản cập nhật mới nhất...")
        req = urllib.request.Request(
            GITHUB_REPO_ZIP,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OmoshiroiUpdater/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as response, open(temp_zip, "wb") as out_file:
            total_size = int(response.info().get("Content-Length", 0))
            downloaded = 0
            block_size = 1024 * 64
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                out_file.write(buffer)
                downloaded += len(buffer)
                if total_size > 0:
                    percent = downloaded * 100 // total_size
                    print(f"\r      Tiến trình tải: {percent}% ({downloaded // 1024} KB / {total_size // 1024} KB)", end="")
                else:
                    print(f"\r      Đã tải: {downloaded // 1024} KB...", end="")
        print("\n      -> Tải bản cập nhật hoàn tất!")

        print("\n[2/4] Đang giải nén mã nguồn mới...")
        if temp_extract.exists():
            shutil.rmtree(temp_extract, ignore_errors=True)
        temp_extract.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(temp_zip, "r") as zip_ref:
            zip_ref.extractall(temp_extract)

        # Thường GitHub zip sẽ nằm trong thư mục omoshiroi-studio-main/
        subdirs = [d for d in temp_extract.iterdir() if d.is_dir()]
        source_dir = subdirs[0] if subdirs else temp_extract

        print("\n[3/4] Đang cập nhật các thành phần hệ thống (Bảo toàn video & API key)...")
        for item_name in UPDATE_TARGETS:
            src_item = source_dir / item_name
            dst_item = PROJECT_ROOT / item_name

            if not src_item.exists():
                continue

            if item_name in PROTECTED_PATHS:
                continue

            if src_item.is_dir():
                if dst_item.exists():
                    shutil.rmtree(dst_item, ignore_errors=True)
                shutil.copytree(src_item, dst_item)
                print(f"      ✓ Đã cập nhật thư mục: {item_name}/")
            else:
                shutil.copy2(src_item, dst_item)
                print(f"      ✓ Đã cập nhật file:    {item_name}")

        print("\n[4/4] Đang kiểm tra và cập nhật các thư viện mới (nếu có)...")
        python_executable = sys.executable
        subprocess.run(
            [python_executable, "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements.txt"), "--quiet"],
            check=False
        )

        print()
        print("=" * 65)
        print("       🎉 CHÚC MỪNG! BẢN NÂNG CẤP MỚI ĐÃ HOÀN TẤT 100%!")
        print("=" * 65)
        print()
        print("  • Toàn bộ tính năng mới đã được áp dụng.")
        print("  • Khóa API Key và toàn bộ Video trong thư mục output/ được giữ nguyên vẹn.")
        print("  👉 Bây giờ bạn có thể mở 'CHAY_TOOL.bat' để sử dụng ngay!")
        print()

    except Exception as e:
        print("\n[LỖI CẬP NHẬT]:", str(e))
        print("Vui lòng kiểm tra kết nối mạng Internet hoặc liên hệ để được hỗ trợ.")
    finally:
        # Dọn dẹp file tạm
        if temp_zip.exists():
            try:
                temp_zip.unlink()
            except Exception:
                pass
        if temp_extract.exists():
            try:
                shutil.rmtree(temp_extract, ignore_errors=True)
            except Exception:
                pass

if __name__ == "__main__":
    download_and_update()
