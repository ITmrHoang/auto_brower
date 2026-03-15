"""
Configuration management for Auto-Browser.
Handles global app config and paths.
"""

import os
import json
from pathlib import Path


class AppConfig:
    """Global application configuration."""

    DEFAULT_CONFIG = {
        "browser_executable": None,  # Auto-detect
        "extensions_dir": "extensions",
        "data_dir": "data",
        "default_window_size": {"width": 800, "height": 600},
        "default_extensions": [],
        "stealth_enabled": True,
    }

    def __init__(self, base_dir: str = None):
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

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def set(self, key: str, value):
        self.config[key] = value
        self.save()

    @property
    def browser_executable(self) -> Path:
        custom = self.config.get("browser_executable")
        if custom:
            return Path(custom)
        # Auto-detect bundled Chromium
        browser_dir = self.base_dir / "browser"
        chrome_exe = browser_dir / "chrome.exe"
        if chrome_exe.exists():
            return chrome_exe
        return None

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
