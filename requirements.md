# 📋 Requirements History

## [2026-03-17] Version 1.0.2 - Xóa dữ liệu Profile an toàn
- **Yêu cầu:** Đảm bảo data của profile browser (cùng lưu trong 1 folder trong project) được xóa (clear) hoàn toàn khi thực hiện lệnh xóa profile để giải phóng bộ nhớ. 
- **Lý do:** Trên Windows, khi xóa thư mục chứa dữ liệu Chromium thường gặp lỗi khóa file (File Lock/Permission Error), khiến rác dữ liệu còn tồn đọng gây đầy ổ cứng. Cần xử lý triệt để việc xóa thư mục này.

## [2026-03-17] Version 1.0.3 - Xóa tận gốc rác Chromium (Deep Cleanup)
- **Yêu cầu:** Bổ sung cơ chế Force Kill và OS-level delete mạnh hơn để dọn sạch 100% rác Chromium/Playwright trong thư mục profile khi user xóa, bao gồm các file rác bị kẹt.
- **Lý do:** Dù đã thêm cơ chế ignore_errors, một số folder Cache của quá trình duy trì Profile vẫn còn xót lại vì file lock ngầm. Cần ép sử dụng trình cmd `rmdir /s /q` của OS khi lệnh Python `shutil.rmtree` thất bại ở bước cuối cùng.

## [2026-03-18] Version 1.0.4 - Chuyển đổi môi trường sang Python 3.12
- **Yêu cầu:** Xóa môi trường `venv` cũ (Python 3.14.3) và tạo lại `venv` với Python 3.12.
- **Lý do:** Phiên bản Python 3.14.3 quá mới, chưa được hỗ trợ bộ mã nhị phân prebuilt wheel cho thư viện `pythonnet` (phụ thuộc của `pywebview`). Điều này dẫn đến lỗi biên dịch bằng Nuget khi chạy `pip install`. Việc đổi sang Python 3.12 sẽ giải quyết dứt điểm lỗi cài đặt.

## [2026-03-18] Version 1.0.5 - Hỗ trợ và Xử lý lỗi Extension Manifest
- **Yêu cầu:** Ghi nhận và hướng dẫn xử lý lỗi "unsupported manifest version" khi Playwright Chromium load extension. Hướng dẫn trích xuất (copy) extension trực tiếp từ trình duyệt web của người dùng sang thư mục `extensions/`.
- **Lý do:** Các bản Chromium mới (đi kèm Playwright đời mới) đã bắt đầu chặn hoặc báo độ trễ mâu thuẫn đối với Manifest V1 / V2. Cần phải load extension định dạng Manifest V3 hoặc copy trọn bộ folder version của extension gốc từ hệ thống.

## [2026-03-18] Version 1.1.0 - GUI: Sync, Script Runner & Script Editor
- **Yêu cầu:** Bổ sung đầy đủ 3 tính năng vào giao diện Desktop GUI:
  1. **Sync Panel:** Chọn Root profile để đồng bộ thao tác sang các Follower.
  2. **Script Runner:** Chạy script từ sidebar với cấu hình loop (vòng lặp) và delay (thời gian chờ giữa các lần lặp).
  3. **Script Editor:** Tạo script JS bằng tay, cài đặt loop/delay, lưu file ra thư mục `scripts/`.
- **Lý do:** Các API backend đã sẵn sàng nhưng GUI chưa expose các tính năng này cho người dùng.

## [2026-03-23] Version 1.1.1 - Fix Type Hint Error in browser_launcher.py
- **Yêu cầu:** Sửa lỗi type hint: `Expression of type "None" cannot be assigned to parameter of type "tuple[Unknown, ...]"`.
- **Lý do:** Đối số `window_size` và `window_position` được gán mặc định là `None` nhưng được đánh dấu kiểu là `tuple` (không được phép trong các công cụ phân tích kiểu nghiêm ngặt).

## [2026-03-23] Version 1.1.2 - Fix NoneType access in browser_launcher.py
- **Yêu cầu:** Sửa lỗi `"get" is not a known attribute of "None"`.
- **Lý do:** Kết quả của `config.get(...)` có thể là `None` nếu giá trị trong JSON là `null`, dẫn đến lỗi khi gọi tiếp `.get()` trên kết quả đó. Cần code an toàn hơn hoặc bổ sung type hints.

## [2026-03-23] Version 1.1.3 - Fix Type Hint in gui_app.py
- **Yêu cầu:** Sửa lỗi: `Type "None" is not assignable to declared type "AppConfig"`.
- **Lý do:** Các biến global (`config`, `profile_mgr`, `launcher`, `sync_engine`) được khởi tạo là `None` nhưng type hint lại là non-nullable. Đổi sang `Optional` và bổ sung safety checks.
