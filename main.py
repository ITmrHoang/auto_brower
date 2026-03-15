#!/usr/bin/env python3
"""
Auto-Browser: CLI Browser Monitoring & Automation

Usage:
    python main.py --help
    python main.py profile create user01 --proxy socks5://127.0.0.1:1080
    python main.py launch user01
    python main.py interactive user01 user02 --sync-root user01
    python main.py chat --agent
"""

import sys
import os
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel

console = Console()


def print_banner():
    """Print the application banner."""
    console.print(Panel.fit(
        "[bold cyan]AUTO-BROWSER[/bold cyan]\n"
        "[dim]CLI Browser Monitoring & Automation v1.0.0[/dim]",
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()


def main():
    print_banner()
    from src.cli import cli
    cli()


if __name__ == "__main__":
    main()
