# 📊 Phân tích kỹ thuật - Auto-Browser

> Cập nhật: 2026-03-16

## 1. Tổng quan dự án

Auto-Browser là ứng dụng CLI & Desktop quản lý đa trình duyệt Chromium sử dụng Python (Playwright, Click, FastAPI, PyWebView). Project có 11 file Python source code trong `src/`, 3 file GUI (HTML/JS/CSS), cùng file `main.py` entry point.

## 2. Phân tích lỗi phát hiện

### 2.1 🔴 Blocker: Máy không cài Python
- Máy không có Python trong PATH → không thể chạy bất kỳ lệnh nào.
- **Giải pháp:** User phải cài Python 3.9+ từ [python.org](https://www.python.org/downloads/) và tích ✅ **Add to PATH**.

### 2.2 🟠 Bug: `generate_script_from_events()` - biến tham chiếu sai
**File:** `src/gui_app.py` dòng 308-314

Khi generate script từ recorded events, biến `el_` sử dụng `len(lines)` tại dòng khai báo (ví dụ `el_8`) nhưng dòng tiếp theo lại dùng `len(lines)` đã tăng lên (`el_9`), dẫn đến click/input sai element.

```python
# BUG: el_ ID khác nhau giữa querySelector và .click()
lines.append(f"  const el_{len(lines)} = document.querySelector(`{s}`);")
lines.append(f"  if (el_{len(lines)}) el_{len(lines)}.click();")
# ↑ len(lines) đã tăng 1 → tham chiếu sai biến!
```

**Fix:** Gán ID vào biến cục bộ trước khi append.

### 2.3 🟠 Bug: `interactive` command thiếu `run_async()` wrapper
**File:** `src/cli.py` dòng 362-418

Hàm `interactive()` tạo coroutine `_interactive()` nhưng **không gọi** `run_async(_interactive())`. Code sẽ không thực thi gì khi user chạy `python main.py interactive ...`.

### 2.4 🟡 Warning: FastAPI deprecated `@app.on_event()`
**File:** `src/gui_app.py` dòng 40, 50

FastAPI >= 0.100 khuyến cáo dùng `lifespan` context manager thay vì `@app.on_event("startup")` / `@app.on_event("shutdown")`. Với phiên bản hiện tại (>=0.100.0 theo requirements.txt), sẽ có deprecation warnings.

### 2.5 🟡 Warning: `delete_profile` API dùng `asyncio.create_task` trong sync context
**File:** `src/gui_app.py` dòng 138

`delete_profile` là sync endpoint nhưng gọi `asyncio.create_task(launcher.close(name))`. Trong context sync, không có event loop chạy → task có thể bị bỏ qua hoặc không thực thi.

### 2.6 🟡 Warning: Pydantic `req.dict()` deprecated
**File:** `src/gui_app.py` dòng 124

Pydantic v2 deprecate `.dict()`, nên dùng `.model_dump()`.

### 2.7 🟢 Minor: `run_async()` có race condition tiềm ẩn
**File:** `src/cli.py` dòng 63-72

`asyncio.get_event_loop()` deprecated trong Python 3.10+. Nên dùng `asyncio.run()` trực tiếp và bắt exception rõ ràng hơn.

## 3. Đánh giá code tổng thể

| Module | Trạng thái | Ghi chú |
|---|---|---|
| `main.py` | ✅ OK | Clean entry point |
| `config.py` | ✅ OK | Solid config pattern |
| `profile_manager.py` | ✅ OK | CRUD sạch sẽ |
| `browser_launcher.py` | ✅ OK | Stealth injection tốt |
| `stealth.py` | ✅ OK | 10 kỹ thuật anti-bot đầy đủ |
| `fingerprint.py` | ✅ OK | Seed-based deterministic |
| `sync_engine.py` | ✅ OK | Event capture + replay tốt |
| `chat_interface.py` | ✅ OK | 20+ commands đầy đủ |
| `agent.py` | ✅ OK | NLP parser VI/EN |
| `cli.py` | 🟠 Bug | Thiếu `run_async` ở `interactive` |
| `gui_app.py` | 🟠 Bug | Variable reference bug + deprecated APIs |
| `gui/` | ✅ OK | Dark mode Glassmorphism UI hoàn chỉnh |

## 4. Phân tích chức năng xóa Profile (Clear Storage)

### 4.1 🔴 Bug: Chromium lock files chống xóa hoàn toàn
**File:** `src/profile_manager.py` (hàm `delete`), `src/cli.py` (lệnh `profile delete`)
User đang gặp lỗi: Khi xóa profile, Playwright (Chromium) tạo ra rất nhiều cache, cache directory và file lock trong Data Profile folder (`data/profile_name`).
Hàm `shutil.rmtree(profile_dir)` trên Windows thường xảy ra lỗi `PermissionError` hoặc `OSError` do file bị khóa hoặc chưa được nhả ngay lập tức, dẫn đến data không được dọn dẹp sạch. Đồng thời với CLI, lệnh `delete` không có cơ chế `force`, không đóng trình duyệt đang chạy, và không bắt ngoại lệ từ OS.

**Giải pháp đề xuất (BA):**
1. Cần viết lại logic xóa thư mục bằng cách bắt lỗi `Exception` (hoặc `OSError`) ở `shutil.rmtree` với thuộc tính `ignore_errors=True` hoặc xử lý vòng lặp force delete.
2. CLI Command `delete` cần có tùy chọn tắt browser đang chạy (báo người dùng) và in thông báo lỗi chính xác thay vì để `ValueError`.
3. Ghi log hoặc cảnh báo rõ khi không dọn sạch được.

### 4.2 🔴 Bug: Python rmtree xoá không sạch rác Chromium (Deep Cleanup)
**File:** `src/profile_manager.py` (hàm `delete`)
Mặc dù đã có `shutil.rmtree` kèm `ignore_errors=True`, nhưng với Chromium trên nền Windows, các tiến trình ngầm (như Crashpad, sub-processes) có thể vẫn cầm handle của thư mục Cache, khiến rác không bị dọn toàn bộ.
**Giải pháp đề xuất (BA):**
Tích hợp lệnh native của Windows `rmdir /s /q` thông qua `os.system` hoặc `subprocess` làm chốt chặn cuối cùng (Fallback Level 3) để ép xóa triệt để cả folder data.

## 5. Quản lý Môi trường Hệ thống

### 5.1 🔴 Blocker: Lỗi cài đặt `pythonnet` do Python quá mới
**Vấn đề:** Khi cài đặt `requirements.txt`, gói `pywebview` thu thập `pythonnet`. Trên thiết bị hiện dùng **Python 3.14.3** - phiên bản quá mới, chưa có prebuilt wheel nhị phân cho `pythonnet` trên Windows. Hệ thống fallback sang build từ source và gặp lỗi chết `nuget.exe update -self` của MSBuild.
**Giải pháp đề xuất (BA):**
1. Bắt buộc xóa bỏ môi trường `venv` hiện tại.
2. Nâng cấp bộ quy chuẩn dự án yêu cầu **Python 3.12** hoặc **3.11** cho độ ổn định.
3. Sử dụng công cụ **`uv` (thiết kế bởi Astral)** để thay thế hoàn toàn `pip` và `venv`. `uv` có khả năng tự fetch độc lập một bản Python 3.12 về máy mà không bị xung đột với hệ thống gốc, gỡ rối hoàn toàn vấn đề Nuget.

### 5.2 🔴 Blocker: Playwright lỗi "unsupported manifest version"
**Vấn đề:** Khi browser launcher nạp thư mục extension `extensions/2.7.20_0`, Chromium trả về lỗi `unsupported manifest version`. Đây là do thư mục bị nạp sai cấp (thiếu `manifest.json` ở thư mục gốc) hoặc extension đó sử dụng Manifest V1/V2 quá cũ, trong khi phiên bản Chromium đi kèm với Playwright 1.58.0 (Chromium 133+) mặc định đã ngưng hỗ trợ hoặc khắt khe với Manifest V2.
**Giải pháp đề xuất (BA):**
1. Cập nhật Extension lên chuẩn Manifest V3.
2. Cung cấp quy trình rõ ràng để người dùng có thể tự copy extension hợp lệ trực tiếp từ `AppData` của Chrome/Edge sang thư mục dự án. Để copy thành công, phải clone nguyên thư mục cha chứa file `manifest.json` chứ không phải thư mục bao ngoài cùng.

---

> **Changelog:**
> - `2026-03-16`: Phân tích lần đầu — Phát hiện 2 bug code (gui_app.py variable ref, cli.py missing run_async), 3 deprecation warnings (FastAPI events, Pydantic .dict(), asyncio get_event_loop), 1 blocker (no Python installed).
> - `2026-03-17`: Phân tích chức năng xóa - Bổ sung lỗi Xóa profile Data do Windows file locking chống xóa, cần cơ chế force delete dọn sạch bộ nhớ.
> - `2026-03-17`: Phân tích Version 1.0.3 - Bổ sung xử lý OS-level force xóa bằng rmdir/rm đối với folder rác Chromium khi các tiến trình ngầm chưa kịp kết thúc.
> - `2026-03-18`: Phân tích Version 1.0.4 - Thay đổi Môi trường Python. Thêm Blocker liên quan đến Python 3.14.3 không tương thích `pywebview` / `pythonnet`. Đề xuất đổi sang Python 3.12.
