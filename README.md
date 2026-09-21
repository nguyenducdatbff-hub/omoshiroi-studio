# OMOSHIROI Studio

Ứng dụng tạo video đối thoại tiếng Nhật khổ dọc 1080 × 1920, kèm phụ đề, giọng đọc, nhạc nền và caption để đăng Shorts/TikTok.

## Cần chuẩn bị

- Python 3.10 trở lên.
- Kết nối Internet để Edge TTS tạo giọng đọc, tải thư viện giao diện từ CDN và tải FFmpeg/FFprobe ở lần dùng đầu tiên nếu máy chưa có sẵn.
- Gemini API Key chỉ cần khi muốn AI viết kịch bản mới theo chủ đề tự nhập.

## Cài và chạy trên Windows

Mở PowerShell tại thư mục dự án, rồi chạy:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe web\app.py
```

Mở <http://127.0.0.1:8001>. Sau khi tạo `.venv`, có thể dùng `run_studio.bat` để mở lại app.

## Cách dùng

1. Chọn cặp nhân vật và kịch bản mẫu, hoặc nhập chủ đề và thêm Gemini API Key để tạo kịch bản mới.
2. Kiểm tra lời thoại tiếng Nhật, bản dịch tiếng Việt, bối cảnh, tốc độ giọng và nhạc nền.
3. Bấm **Xuất bản video Shorts**. Mỗi lần xuất tạo một thư mục riêng trong `output/`, chứa MP4 và `caption.txt`.

Khi không có API Key, app tải kịch bản mẫu theo cặp nhân vật; chủ đề mới chưa được áp dụng. Key được lưu trong trình duyệt và chỉ được kiểm tra khi bấm **Tạo Kịch Bản**. Nếu Gemini từ chối key, model hoặc hạn mức, app hiện lý do ngay dưới ô chủ đề để bạn xử lý trong Google AI Studio.

## Kiểm tra nhanh

```powershell
.\.venv\Scripts\python.exe test_app_smoke.py
node test_ui_smoke.cjs
```

Quá trình tạo MP4 cần FFmpeg, Edge TTS và Internet. Server mặc định lắng nghe tại `127.0.0.1:8001`.
