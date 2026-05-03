"""
Profile Manager for Auto-Browser.
Create, list, delete browser profiles with proxy configuration.
"""

import json
import shutil
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

from .fingerprint import generate_fingerprint
from rich.console import Console
from rich.table import Table

console = Console()


class ProfileManager:
    """Manages browser profiles with proxy and fingerprint configs."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _profile_dir(self, name: str) -> Path:
        return self.data_dir / name

    def _profile_config_path(self, name: str) -> Path:
        return self._profile_dir(name) / "profile.json"

    def _generate_id(self) -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    def create(self, name: str, proxy: Optional[str] = None,
               proxy_username: Optional[str] = None, proxy_password: Optional[str] = None,
               user_agent: Optional[str] = None, notes: str = "",
               browser_path: Optional[str] = None, browser_name: Optional[str] = None) -> dict:
        """Create a new browser profile."""
        profile_dir = self._profile_dir(name)
        if profile_dir.exists():
            raise ValueError(f"Profile '{name}' already exists")

        profile_dir.mkdir(parents=True, exist_ok=True)

        # Xây dựng URL Proxy để truyền cho Fingerprint API
        proxy_url = proxy
        if proxy and proxy_username and proxy_password:
            # Format: http://user:pass@ip:port
            if "://" in proxy:
                schema, rest = proxy.split("://", 1)
                proxy_url = f"{schema}://{proxy_username}:{proxy_password}@{rest}"
            else:
                proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy}"

        profile = {
            "id": self._generate_id(),
            "name": name,
            "proxy": proxy,
            "proxy_username": proxy_username,
            "proxy_password": proxy_password,
            "user_agent": user_agent,
            "notes": notes,
            "browser_path": browser_path or "",
            "browser_name": browser_name or "",
            "fingerprint": generate_fingerprint(seed=name, proxy=proxy_url, custom_user_agent=user_agent),
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "extensions": [],
        }

        with open(self._profile_config_path(name), "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        return profile

    def get(self, name: str) -> Optional[dict]:
        """Get profile configuration."""
        config_path = self._profile_config_path(name)
        if not config_path.exists():
            return None
        with open(config_path, "r", encoding="utf-8") as f:
            profile = json.load(f)
            
        # Tự động vá lỗi (Self-heal) cho các profile cũ chưa có fingerprint
        if not profile.get("fingerprint"):
            # Xây dựng proxy URL nếu có để gen fingerprint chuẩn Location
            proxy_url = profile.get("proxy")
            user = profile.get("proxy_username")
            pw = profile.get("proxy_password")
            if proxy_url and user and pw:
                if "://" in proxy_url:
                    schema, rest = proxy_url.split("://", 1)
                    proxy_url = f"{schema}://{user}:{pw}@{rest}"
                else:
                    proxy_url = f"http://{user}:{pw}@{proxy_url}"
                    
            profile["fingerprint"] = generate_fingerprint(seed=name, proxy=proxy_url, custom_user_agent=profile.get("user_agent"))
            with open(config_path, "w", encoding="utf-8") as f2:
                json.dump(profile, f2, indent=2, ensure_ascii=False)
                
        return profile

    def update(self, name: str, **kwargs):
        """Update profile configuration."""
        profile = self.get(name)
        if not profile:
            raise ValueError(f"Profile '{name}' not found")
            
        # Nếu có hành động liên quan tới cập nhật / xoá Proxy HOẶC Đổi UserAgent, ta sẽ tái tạo lại Cấu trúc Fingerprint cho PHÙ HỢP
        update_keys = ["proxy", "proxy_username", "proxy_password", "user_agent"]
        if any(k in kwargs for k in update_keys):
            p_url = kwargs.get("proxy", profile.get("proxy"))
            user = kwargs.get("proxy_username", profile.get("proxy_username"))
            pw = kwargs.get("proxy_password", profile.get("proxy_password"))
            custom_ua = kwargs.get("user_agent", profile.get("user_agent"))
            
            req_proxy = p_url
            if p_url and user and pw:
                if "://" in p_url:
                    schema, rest = p_url.split("://", 1)
                    req_proxy = f"{schema}://{user}:{pw}@{rest}"
                else:
                    req_proxy = f"http://{user}:{pw}@{p_url}"
                    
            profile["fingerprint"] = generate_fingerprint(seed=name, proxy=req_proxy, custom_user_agent=custom_ua)
            
        profile.update(kwargs)
        with open(self._profile_config_path(name), "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        return profile

    def delete(self, name: str):
        """Delete a profile and all its data."""
        profile_dir = self._profile_dir(name)
        if not profile_dir.exists():
            raise ValueError(f"Profile '{name}' not found")
            
        import time
        import platform
        import subprocess
        max_retries = 3
        for i in range(max_retries):
            try:
                shutil.rmtree(profile_dir)
                break
            except Exception as e:
                time.sleep(1)
                if i == max_retries - 1:
                    # Last resort, try to remove ignoring errors to clear at least most of the data
                    shutil.rmtree(profile_dir, ignore_errors=True)
                    
        # Deep Cleanup (v1.0.3): Check if folder still exists (e.g locked files by OS)
        if profile_dir.exists():
            console.print(f"[yellow]Python shutil couldn't fully clear '{profile_dir}'. Escalating to OS deep cleanup...[/yellow]")
            try:
                if platform.system() == "Windows":
                    # Use native Windows command to force remove directory
                    subprocess.run(
                        f'rmdir /s /q "{profile_dir}"', 
                        shell=True,
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    subprocess.run(
                        f'rm -rf "{profile_dir}"',
                        shell=True,
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                
                # Final check after OS level delete
                if profile_dir.exists():
                    console.print(f"[red]Warning: Some files in '{profile_dir}' are permanently locked by the OS and couldn't be deleted.[/red]")
            except Exception as e:
                console.print(f"[red]OS-level cleanup failed: {e}[/red]")

    def list_profiles(self) -> List[dict]:
        """List all profiles."""
        profiles = []
        if not self.data_dir.exists():
            return profiles
        for item in sorted(self.data_dir.iterdir()):
            if item.is_dir():
                config_path = item / "profile.json"
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        profiles.append(json.load(f))
                else:
                    # Legacy profile without config
                    profiles.append({
                        "name": item.name,
                        "proxy": None,
                        "created_at": "unknown",
                        "last_used": None,
                    })
        return profiles

    def set_proxy(self, name: str, proxy_url: Optional[str]):
        """Set or remove proxy for a profile."""
        return self.update(name, proxy=proxy_url)

    def display_profiles(self):
        """Display profiles in a rich table."""
        profiles = self.list_profiles()
        if not profiles:
            console.print("[yellow]No profiles found.[/yellow]")
            return

        table = Table(title="🌐 Browser Profiles", show_lines=True)
        table.add_column("Name", style="cyan bold")
        table.add_column("Proxy", style="green")
        table.add_column("User Agent", style="dim", max_width=40)
        table.add_column("Created", style="magenta")
        table.add_column("Last Used", style="blue")

        for p in profiles:
            table.add_row(
                p.get("name", "?"),
                p.get("proxy") or "[dim]none[/dim]",
                (p.get("user_agent") or "[dim]default[/dim]")[:40],
                p.get("created_at", "?")[:19],
                (p.get("last_used") or "[dim]never[/dim]")[:19] if p.get("last_used") else "[dim]never[/dim]",
            )

        console.print(table)
