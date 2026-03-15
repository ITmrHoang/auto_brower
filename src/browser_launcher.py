"""
Browser Launcher for Auto-Browser.
Launches and manages browser instances with stealth, proxy, and fingerprint support.
Uses Playwright for browser automation.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from rich.console import Console
from rich.table import Table

from .config import AppConfig
from .stealth import get_combined_stealth_script
from .fingerprint import generate_fingerprint, fingerprint_to_stealth_script

console = Console()


class BrowserInstance:
    """Represents a running browser instance."""

    def __init__(self, profile_name: str, context, browser, pages=None):
        self.profile_name = profile_name
        self.context = context
        self.browser = browser
        self.pages = pages or []
        self.launched_at = datetime.now()

    @property
    def active_page(self):
        if self.pages:
            return self.pages[-1]
        return None

    async def get_current_url(self) -> str:
        page = self.active_page
        if page:
            try:
                return page.url
            except Exception:
                return "unknown"
        return "no page"


class BrowserLauncher:
    """Manages launching and tracking browser instances."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.instances: Dict[str, BrowserInstance] = {}
        self._playwright = None

    async def _ensure_playwright(self):
        """Initialize playwright if needed."""
        if self._playwright is None:
            from playwright.async_api import async_playwright
            self._playwright_cm = async_playwright()
            self._playwright = await self._playwright_cm.__aenter__()
        return self._playwright

    async def launch(self, profile_name: str, profile_config: dict,
                     headless: bool = False,
                     window_size: tuple = None,
                     window_position: tuple = None) -> BrowserInstance:
        """Launch a browser with the given profile configuration."""
        if profile_name in self.instances:
            raise ValueError(f"Browser for profile '{profile_name}' is already running")

        pw = await self._ensure_playwright()

        # Build launch args
        args = [
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
        ]

        # Window size
        ws = window_size or (
            self.config.get("default_window_size", {}).get("width", 800),
            self.config.get("default_window_size", {}).get("height", 600)
        )
        args.append(f"--window-size={ws[0]},{ws[1]}")

        # Window position
        if window_position:
            args.append(f"--window-position={window_position[0]},{window_position[1]}")

        # Proxy
        proxy_config = None
        proxy_url = profile_config.get("proxy")
        if proxy_url:
            proxy_config = {"server": proxy_url}
            proxy_user = profile_config.get("proxy_username")
            proxy_pass = profile_config.get("proxy_password")
            if proxy_user and proxy_pass:
                proxy_config["username"] = proxy_user
                proxy_config["password"] = proxy_pass

        # Extensions
        ext_paths = self.config.get_extension_paths()
        if ext_paths:
            args.append(f"--disable-extensions-except={','.join(ext_paths)}")
            args.append(f"--load-extension={','.join(ext_paths)}")

        # User data dir
        user_data_dir = str(self.config.data_dir / profile_name)

        # Fingerprint
        fingerprint = profile_config.get("fingerprint")
        if not fingerprint:
            fingerprint = generate_fingerprint(seed=profile_name)

        user_agent = profile_config.get("user_agent") or fingerprint.get("user_agent")

        # Launch persistent context
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=str(self.config.browser_executable) if self.config.browser_executable else None,
            headless=headless,
            args=args,
            proxy=proxy_config,
            user_agent=user_agent,
            viewport={"width": ws[0], "height": ws[1]},
            ignore_default_args=["--enable-automation"],
            color_scheme="dark",
        )

        # Inject stealth scripts on every new page
        stealth_script = get_combined_stealth_script()
        fp_script = fingerprint_to_stealth_script(fingerprint)

        async def inject_stealth(page):
            try:
                await page.add_init_script(stealth_script)
                await page.add_init_script(fp_script)
            except Exception:
                pass

        # Inject stealth into existing pages
        for page in context.pages:
            await inject_stealth(page)

        # Listen for new pages
        context.on("page", lambda page: asyncio.ensure_future(inject_stealth(page)))

        instance = BrowserInstance(
            profile_name=profile_name,
            context=context,
            browser=None,
            pages=list(context.pages),
        )

        # Track new pages
        def on_page(page):
            instance.pages.append(page)
            page.on("close", lambda: instance.pages.remove(page) if page in instance.pages else None)

        context.on("page", on_page)

        self.instances[profile_name] = instance
        console.print(f"[green]✓[/green] Launched browser for profile [cyan]{profile_name}[/cyan]")

        return instance

    async def close(self, profile_name: str):
        """Close a browser instance."""
        instance = self.instances.get(profile_name)
        if not instance:
            raise ValueError(f"No running browser for profile '{profile_name}'")
        try:
            await instance.context.close()
        except Exception:
            pass
        del self.instances[profile_name]
        console.print(f"[red]✗[/red] Closed browser for profile [cyan]{profile_name}[/cyan]")

    async def close_all(self):
        """Close all running browser instances."""
        names = list(self.instances.keys())
        for name in names:
            await self.close(name)

    async def shutdown(self):
        """Shutdown playwright."""
        await self.close_all()
        if self._playwright:
            await self._playwright_cm.__aexit__(None, None, None)
            self._playwright = None

    def get_instance(self, profile_name: str) -> Optional[BrowserInstance]:
        return self.instances.get(profile_name)

    def list_running(self) -> list:
        return list(self.instances.keys())

    async def display_status(self):
        """Display running browsers in a rich table."""
        if not self.instances:
            console.print("[yellow]No browsers running.[/yellow]")
            return

        table = Table(title="🖥️  Running Browsers", show_lines=True)
        table.add_column("Profile", style="cyan bold")
        table.add_column("URL", style="green", max_width=60)
        table.add_column("Pages", style="magenta")
        table.add_column("Launched", style="blue")

        for name, inst in self.instances.items():
            url = await inst.get_current_url()
            table.add_row(
                name,
                url[:60],
                str(len(inst.pages)),
                inst.launched_at.strftime("%H:%M:%S"),
            )

        console.print(table)
