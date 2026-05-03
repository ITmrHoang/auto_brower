"""
Configuration management for Auto-Browser.
Handles global app config and paths.
"""

import os
import json
from pathlib import Path
from typing import Optional, Any, List, Dict


# Danh sách đường dẫn phổ biến của các trình duyệt trên Windows
BROWSER_SEARCH_PATHS: List[Dict[str, Any]] = [
    {
        "name": "Google Chrome",
        "engine": "chromium",
        "paths": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ]
    },
    {
        "name": "Microsoft Edge",
        "engine": "chromium",
        "paths": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ]
    },
    {
        "name": "Brave Browser",
        "engine": "chromium",
        "paths": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
        ]
    },
    {
        "name": "Vivaldi",
        "engine": "chromium",
        "paths": [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Vivaldi" / "Application" / "vivaldi.exe",
        ]
    },
    {
        "name": "Opera",
        "engine": "chromium",
        "paths": [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Opera" / "opera.exe",
        ]
    },
]


class AppConfig:
    """Global application configuration."""

    DEFAULT_CONFIG = {
        "browser_executable": None,  # Auto-detect
        "browser_name": None,  # Tên trình duyệt đang chọn (hiển thị trên UI)
        "extensions_dir": "extensions",
        "data_dir": "data",
        "default_window_size": {"width": 800, "height": 600},
        "default_extensions": [],
        "stealth_enabled": True,
        "randomize_viewport": True,
    }

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_file = self.base_dir / "config.json"
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                return {**self.DEFAULT_CONFIG, **saved}
        return dict(self.DEFAULT_CONFIG)

    def save(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Lấy giá trị từ cấu hình với giá trị mặc định nếu không tồn tại (null-safe)."""
        val = self.config.get(key, default)
        return val if val is not None else default

    def set(self, key: str, value):
        self.config[key] = value
        self.save()

    def detect_installed_browsers(self) -> List[Dict[str, str]]:
        """Quét tìm tất cả trình duyệt đã cài trên PC cùng Chromium cục bộ trong project."""
        found = []

        # 1. Ưu tiên Chromium cục bộ trong thư mục project (nếu có)
        local_chrome = self.base_dir / "browser" / "chrome.exe"
        if local_chrome.exists():
            found.append({
                "name": "Chromium (Local)",
                "engine": "chromium",
                "path": str(local_chrome)
            })

        # 2. Quét các trình duyệt đã cài trên Windows
        for browser_info in BROWSER_SEARCH_PATHS:
            for p in browser_info["paths"]:
                if p.exists():
                    found.append({
                        "name": browser_info["name"],
                        "engine": browser_info["engine"],
                        "path": str(p)
                    })
                    break  # Chỉ lấy path đầu tiên tìm được cho mỗi loại trình duyệt

        # 3. Playwright Chromium mặc định (luôn có sẵn, không cần path)
        found.append({
            "name": "Playwright Chromium (Built-in)",
            "engine": "chromium",
            "path": ""  # Rỗng = dùng Chromium mặc định của Playwright
        })

        return found

    def set_browser(self, browser_path: str, browser_name: str):
        """Đặt trình duyệt sử dụng cho project."""
        self.config["browser_executable"] = browser_path if browser_path else None
        self.config["browser_name"] = browser_name
        self.save()

    @property
    def browser_executable(self) -> Optional[Path]:
        custom = self.config.get("browser_executable")
        if custom:
            p = Path(custom)
            if p.exists():
                return p

        # Auto-detect: Ưu tiên Chromium cục bộ → Chrome trên PC → Playwright mặc định
        local_chrome = self.base_dir / "browser" / "chrome.exe"
        if local_chrome.exists():
            return local_chrome

        # Tìm Google Chrome hoặc Edge trên PC
        for browser_info in BROWSER_SEARCH_PATHS:
            for p in browser_info["paths"]:
                if p.exists():
                    return p

        # Fallback: Dùng Chromium mặc định của Playwright (trả về None)
        return None

    @property
    def browser_display_name(self) -> str:
        """Tên trình duyệt hiện tại để hiển thị trên UI."""
        name = self.config.get("browser_name")
        if name:
            return name
        # Tự suy ra tên từ executable path
        exe = self.browser_executable
        if exe is None:
            return "Playwright Chromium (Built-in)"
        exe_str = str(exe).lower()
        if "brave" in exe_str:
            return "Brave Browser"
        if "msedge" in exe_str:
            return "Microsoft Edge"
        if "vivaldi" in exe_str:
            return "Vivaldi"
        if "opera" in exe_str:
            return "Opera"
        if "browser" in exe_str and str(self.base_dir).lower() in exe_str:
            return "Chromium (Local)"
        return "Google Chrome"

    @property
    def extensions_dir(self) -> Path:
        return self.base_dir / self.config["extensions_dir"]

    @property
    def data_dir(self) -> Path:
        d = self.base_dir / self.config["data_dir"]
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def scripts_dir(self) -> Path:
        d = self.base_dir / "scripts"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_extension_paths(self) -> list:
        """Get all available extension paths."""
        ext_dir = self.extensions_dir
        if not ext_dir.exists():
            return []
        paths = []
        for item in ext_dir.iterdir():
            if item.is_dir() and (item / "manifest.json").exists():
                paths.append(str(item))
        return paths
