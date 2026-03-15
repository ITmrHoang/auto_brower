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
               user_agent: Optional[str] = None, notes: str = "") -> dict:
        """Create a new browser profile."""
        profile_dir = self._profile_dir(name)
        if profile_dir.exists():
            raise ValueError(f"Profile '{name}' already exists")

        profile_dir.mkdir(parents=True, exist_ok=True)

        profile = {
            "id": self._generate_id(),
            "name": name,
            "proxy": proxy,
            "proxy_username": proxy_username,
            "proxy_password": proxy_password,
            "user_agent": user_agent,
            "notes": notes,
            "fingerprint": None,  # Will be generated on first launch
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
            return json.load(f)

    def update(self, name: str, **kwargs):
        """Update profile configuration."""
        profile = self.get(name)
        if not profile:
            raise ValueError(f"Profile '{name}' not found")
        profile.update(kwargs)
        with open(self._profile_config_path(name), "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        return profile

    def delete(self, name: str):
        """Delete a profile and all its data."""
        profile_dir = self._profile_dir(name)
        if not profile_dir.exists():
            raise ValueError(f"Profile '{name}' not found")
        shutil.rmtree(profile_dir)

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
