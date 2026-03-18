# 🌐 Auto-Browser

Ứng dụng CLI & Desktop quản lý đa trình duyệt Chromium với hỗ trợ **anti-bot**, **proxy riêng**, **đồng bộ thao tác**, và **ghi lại hành động tự động**.

---

## ✨ Tính năng chính

| Tính năng | Mô tả |
|---|---|
| 🧑‍💼 **Quản lý Profile** | Tạo, sửa, xóa profile trình duyệt riêng biệt với proxy riêng |
| 🔒 **Proxy Authentication** | Hỗ trợ HTTP/SOCKS5 proxy có username & password |
| 🕵️ **Anti-Bot Stealth** | 10 kỹ thuật chống phát hiện bot (WebGL, Canvas, WebRTC, Navigator...) |
| 🎭 **Fingerprint** | Tự động tạo fingerprint ngẫu nhiên nhưng nhất quán cho mỗi profile |
| 🔄 **Sync Engine** | Đồng bộ thao tác từ trình duyệt Root sang các trình duyệt Follower |
| 🎥 **Record & Play** | Ghi lại thao tác thành file `.js`, chạy lại trên bất kỳ profile nào |
| 💬 **Chat Interface** | Gõ lệnh điều khiển trình duyệt bằng text (hỗ trợ Tiếng Việt) |
| 🖥️ **Desktop GUI** | Giao diện Desktop Dark Mode (FastAPI + PyWebView) |

---

## 📦 Cài đặt

### Yêu cầu
- Python 3.11 hoặc 3.12 (Bắt buộc dùng bản này để cài đặt thư viện giao diện Desktop GUI. **Không dùng Python 3.13 hoặc 3.14**)
- Windows 10/11

### Bước 1: Clone repository

```bash
git clone <repo-url>
cd auto-brower
```

### Bước 2: Tạo môi trường ảo (Khuyên dùng)

Sử dụng môi trường ảo (`venv`) giúp tránh xung đột thư viện với hệ thống và đặc biệt cần thiết trên Windows để cài đặt các package GUI một cách trơn tru.

```bash
# Cài đặt công cụ uv siêu tốc (nếu máy chưa có)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Tạo môi trường ảo tự động tải Python 3.12 (không cần cài Python vào máy)
uv venv --python 3.12 venv

# Kích hoạt môi trường ảo (trên CMD)
venv\Scripts\activate
# Hoặc trên PowerShell: 
# .\venv\Scripts\Activate
```

### Bước 3: Cài đặt thư viện bằng uv pip

```bash
uv pip install -r requirements.txt
```

### Bước 4: Cài Playwright browser (lần đầu)

```bash
playwright install chromium
```

> **Lưu ý:** Nếu bạn đã có file `chrome-win.zip` hoặc thư mục `browser/` chứa Chromium tùy chỉnh, ứng dụng sẽ tự động sử dụng nó thay vì Chromium mặc định của Playwright.

---

## 🚀 Cách sử dụng

### Chế độ Desktop GUI (Khuyên dùng)

```bash
python main.py gui
```

Một cửa sổ ứng dụng sẽ mở ra với giao diện quản lý trực quan:
- **Sidebar trái**: Danh sách profile & script
- **Panel chính**: Thông tin chi tiết, nút Launch/Close, Record

### Chế độ CLI

#### Quản lý Profile

```bash
# Tạo profile mới
python main.py profile create taikhoan01

# Tạo profile có proxy
python main.py profile create taikhoan01 --proxy socks5://ip:port

# Xem danh sách profile
python main.py profile list

# Cài proxy cho profile có sẵn
python main.py profile set-proxy taikhoan01 http://ip:port

# Xóa profile
python main.py profile delete taikhoan01
```

#### Mở trình duyệt

```bash
# Mở 1 hoặc nhiều profile
python main.py launch taikhoan01 taikhoan02
```

#### Đồng bộ thao tác (Sync)

```bash
# Đặt taikhoan01 làm Root, các profile còn lại tự động làm theo
python main.py sync start --root taikhoan01 -f taikhoan02 -f taikhoan03
```

#### Chat điều khiển

```bash
# Chế độ tương tác (mở browser + chat)
python main.py interactive taikhoan01 taikhoan02

# Chat có AI agent hỗ trợ Tiếng Việt
python main.py chat --agent
```

#### Chạy script

```bash
# Chạy script JS đã ghi từ Record
python main.py run auto_login.js --target taikhoan01
```

---

## 🔧 Cấu hình Proxy

Ứng dụng hỗ trợ proxy mua từ bất kỳ nhà cung cấp nào. Khi tạo profile qua GUI hoặc CLI, bạn có thể nhập:

| Trường | Ví dụ | Mô tả |
|---|---|---|
| **Proxy URL** | `socks5://1.2.3.4:1080` | Địa chỉ proxy server |
| **Proxy Username** | `user123` | Tên đăng nhập (nếu proxy yêu cầu) |
| **Proxy Password** | `pass456` | Mật khẩu (nếu proxy yêu cầu) |

Các định dạng proxy được hỗ trợ:
- `http://ip:port`
- `https://ip:port`
- `socks5://ip:port`

---

## 🛡️ Anti-Bot Stealth

Hệ thống tự động inject 10 kỹ thuật chống phát hiện bot vào mỗi trang:

1. Xóa `navigator.webdriver`
2. Giả lập plugin trình duyệt
3. Fake WebGL vendor/renderer
4. Thêm nhiễu Canvas fingerprint
5. Chặn rò rỉ IP qua WebRTC
6. Mock Chrome runtime API
7. Override Permissions API
8. Giả lập thông số CPU/RAM
9. Override ngôn ngữ trình duyệt
10. Bypass phát hiện iframe

---

## 📂 Cấu trúc thư mục

```
auto-brower/
├── main.py                 # Entry point
├── requirements.txt        # Thư viện Python
├── gui/
│   ├── index.html          # Giao diện Desktop
│   ├── style.css           # Styling (Dark Mode)
│   └── app.js              # Logic frontend
├── src/
│   ├── cli.py              # CLI commands (Click)
│   ├── gui_app.py          # FastAPI backend cho GUI
│   ├── config.py           # Quản lý cấu hình
│   ├── profile_manager.py  # CRUD profile
│   ├── browser_launcher.py # Khởi chạy browser (Playwright)
│   ├── stealth.py          # Anti-bot scripts
│   ├── fingerprint.py      # Tạo fingerprint
│   ├── sync_engine.py      # Đồng bộ + ghi thao tác
│   ├── chat_interface.py   # Chat điều khiển
│   └── agent.py            # NLP parser (VI/EN)
├── extensions/             # Chrome extensions (VPN, uBlock...)
├── browser/                # Chromium binary (không commit)
├── data/                   # Profile data (không commit)
└── scripts/                # Script đã ghi (không commit)
```

---

## 💬 Lệnh Chat hỗ trợ

| Lệnh | Mô tả |
|---|---|
| `goto <url>` | Mở URL |
| `click <selector>` | Click phần tử |
| `type <selector> <text>` | Gõ chữ vào ô input |
| `fill <selector> <text>` | Điền giá trị vào input |
| `press <key>` | Nhấn phím (Enter, Tab...) |
| `scroll <x> <y>` | Cuộn trang |
| `screenshot` | Chụp màn hình |
| `eval <js>` | Chạy JavaScript |
| `script <file>` | Chạy file script |
| `wait <ms>` | Chờ (milliseconds) |
| `select <profile>` | Chọn profile đang hoạt động |
| `list` | Liệt kê browser đang mở |
| `url` | Xem URL hiện tại |
| `back` / `forward` | Điều hướng lịch sử |
| `reload` | Tải lại trang |
| `close` | Đóng browser hiện tại |

---

## 📝 License

MIT
