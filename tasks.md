# 📋 Tasks - Auto-Browser

> Cập nhật: 2026-03-23

## Module: Bug Fixes & Code Quality (v1.0.1)

- [x] **Task 1:** Fix `generate_script_from_events()` biến tham chiếu sai trong `gui_app.py`
- [x] **Task 2:** Fix `interactive` command thiếu `run_async()` trong `cli.py`
- [x] **Task 3:** Fix FastAPI deprecated `@app.on_event()` → dùng `lifespan` context manager
- [x] **Task 4:** Fix `delete_profile` API — chuyển từ sync sang async endpoint
- [x] **Task 5:** Fix Pydantic deprecated `.dict()` → `.model_dump()`
- [x] **Task 6:** Cải thiện `run_async()` helper — ưu tiên `asyncio.run()` trực tiếp
- [x] **Task 7:** Cài đặt Python & dependencies, chạy test xác minh toàn bộ

## Module: Xóa dữ liệu Profile hoàn toàn (v1.0.2 & v1.0.3)
- [x] **Task 8:** Cập nhật hàm `delete` trong `ProfileManager` để có cơ chế force rmtree trên Windows, handling `OSError`.
- [x] **Task 9:** Sửa lệnh CLI `delete` để bắt lỗi khi không dọn được data directory, trước khi xóa cảnh báo/kill browser nếu nó đang mở.
- [x] **Task 10 (Deep Cleanup):** Thêm cơ chế OS-level remove (`rmdir /s /q`) vào cuối hàm `delete` của `ProfileManager` để ép dọn sạch cả khi Python `shutil` thất bại (chặn xót file rác/cache list).

## Module: Nâng cấp Môi trường Hệ thống (v1.0.4)
- [x] **Task 11:** Xóa môi trường `venv` cũ (Python 3.14.3) gây lỗi cài đặt
- [x] **Task 12:** Cài đặt công cụ `uv` để quản lý môi trường (Thay thế pip và venv mặc định)
- [x] **Task 13:** Dùng `uv` tự động tải Python 3.12 cô lập, tạo `venv` và cài đặt `requirements.txt` siêu tốc

## Module: Xử lý Extension (v1.0.5)
- [x] **Task 14:** Phân tích nguyên nhân lỗi `unsupported manifest version` do thay đổi chính sách Chromium (Manifest V3) hoặc sai path.
- [x] **Task 15:** Điều xuất (Log) hướng dẫn để User có thể tự fetch Extension từ Google Chrome local sang project `auto_brower`.

## Module: GUI - Sync, Script Runner & Editor (v1.1.0)
- [x] **Task 16:** Thêm endpoint `POST /api/scripts/save` và nâng cấp `POST /api/scripts/run` hỗ trợ loop/delay (`gui_app.py`)
- [x] **Task 17:** Thêm Sync Panel Card, Script Runner Modal, Script Editor Modal vào `index.html`
- [x] **Task 18:** Thêm logic JS cho sync, script runner, script editor vào `app.js`
- [x] **Task 19:** Thêm CSS cho các component mới vào `style.css`
- [x] **Task 20:** Tách vòng đời GUI window ra khỏi Server — tắt GUI không tắt app, chỉ Ctrl+C mới tắt

## Module: Phát triển và Bảo trì (v1.1.1, v1.1.2 & v1.1.3)
- [x] **Task 21:** Sửa lỗi type hint `window_size` và `window_position` trong `src\browser_launcher.py` thành `Optional[tuple]`.
- [x] **Task 22:** Sửa lỗi type hint cho `proxy` trong `src\browser_launcher.py` bằng cách sử dụng `ProxySettings`.
- [x] **Task 23:** Fix lỗi "get" is not a known attribute of "None" trong `src\browser_launcher.py` (L87).
- [x] **Task 24:** Sửa lỗi Type Hint cho các biến global (`config`, `profile_mgr`, etc.) trong `src\gui_app.py`.
