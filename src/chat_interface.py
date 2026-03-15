"""
Chat Interface for Auto-Browser.
Interactive command-line interface to control browsers with text commands and scripts.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

console = Console()

HELP_TEXT = """
## 🎮 Browser Chat Commands

| Command | Description |
|---|---|
| `goto <url>` | Navigate to URL (all browsers or specify `@profile`) |
| `click <selector>` | Click an element by CSS selector |
| `type <selector> <text>` | Type text into an element |
| `fill <selector> <text>` | Fill input (clears first) |
| `press <key>` | Press a key (Enter, Tab, etc.) |
| `scroll <x> <y>` | Scroll to position |
| `screenshot [filename]` | Take screenshot |
| `eval <js_code>` | Execute JavaScript code |
| `script <file.js>` | Run a JavaScript file |
| `wait <ms>` | Wait for milliseconds |
| `select <profile>` | Select target browser |
| `select all` | Target all browsers |
| `list` | List running browsers |
| `url` | Show current URL |
| `back` | Go back |
| `forward` | Go forward |
| `reload` | Reload page |
| `close [profile]` | Close a browser |
| `help` | Show this help |
| `exit` / `quit` | Exit chat |
"""


class ChatInterface:
    """Interactive chat for browser control."""

    def __init__(self, browser_launcher, sync_engine=None):
        self.launcher = browser_launcher
        self.sync = sync_engine
        self.target_profile: Optional[str] = None  # None = all
        self.session = PromptSession(
            history=InMemoryHistory(),
            auto_suggest=AutoSuggestFromHistory(),
        )

    def _get_target_pages(self) -> list:
        """Get pages to operate on based on current target."""
        if self.target_profile:
            inst = self.launcher.get_instance(self.target_profile)
            if inst and inst.active_page:
                return [(self.target_profile, inst.active_page)]
            return []
        else:
            pages = []
            for name in self.launcher.list_running():
                inst = self.launcher.get_instance(name)
                if inst and inst.active_page:
                    pages.append((name, inst.active_page))
            return pages

    async def _exec_on_targets(self, coro_factory):
        """Execute an async operation on all target pages."""
        pages = self._get_target_pages()
        if not pages:
            console.print("[yellow]No target browsers available[/yellow]")
            return

        tasks = []
        for name, page in pages:
            tasks.append(self._safe_exec(name, page, coro_factory))
        await asyncio.gather(*tasks)

    async def _safe_exec(self, name, page, coro_factory):
        try:
            result = await coro_factory(page)
            if result is not None:
                console.print(f"[cyan]{name}[/cyan] → {result}")
        except Exception as e:
            console.print(f"[red]{name}[/red] → Error: {e}")

    async def handle_command(self, cmd: str) -> bool:
        """
        Handle a single command. Returns False if should exit.
        """
        cmd = cmd.strip()
        if not cmd:
            return True

        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Check for @profile prefix
        if command.startswith("@"):
            profile = command[1:]
            if profile in self.launcher.list_running():
                self.target_profile = profile
                console.print(f"[cyan]Targeting: {profile}[/cyan]")
                if args:
                    return await self.handle_command(args)
            else:
                console.print(f"[red]Profile '{profile}' not found[/red]")
            return True

        if command in ("exit", "quit", "q"):
            return False

        elif command == "help":
            console.print(Markdown(HELP_TEXT))

        elif command == "goto" and args:
            url = args if args.startswith("http") else f"https://{args}"
            await self._exec_on_targets(
                lambda page: page.goto(url, wait_until="domcontentloaded", timeout=30000)
            )
            console.print(f"[green]→ Navigated to {url}[/green]")

        elif command == "click" and args:
            await self._exec_on_targets(
                lambda page, s=args: page.click(s, timeout=5000)
            )

        elif command == "type" and args:
            parts = args.split(maxsplit=1)
            if len(parts) == 2:
                selector, text = parts
                await self._exec_on_targets(
                    lambda page, s=selector, t=text: page.type(s, t)
                )
            else:
                console.print("[red]Usage: type <selector> <text>[/red]")

        elif command == "fill" and args:
            parts = args.split(maxsplit=1)
            if len(parts) == 2:
                selector, text = parts
                await self._exec_on_targets(
                    lambda page, s=selector, t=text: page.fill(s, t)
                )
            else:
                console.print("[red]Usage: fill <selector> <text>[/red]")

        elif command == "press" and args:
            await self._exec_on_targets(
                lambda page, k=args: page.keyboard.press(k)
            )

        elif command == "scroll" and args:
            parts = args.split()
            if len(parts) == 2:
                x, y = int(parts[0]), int(parts[1])
                await self._exec_on_targets(
                    lambda page, sx=x, sy=y: page.evaluate(f"window.scrollTo({sx}, {sy})")
                )
            else:
                console.print("[red]Usage: scroll <x> <y>[/red]")

        elif command == "screenshot":
            filename = args or "screenshot.png"
            pages = self._get_target_pages()
            for name, page in pages:
                try:
                    path = f"screenshots/{name}_{filename}"
                    os.makedirs("screenshots", exist_ok=True)
                    await page.screenshot(path=path, full_page=True)
                    console.print(f"[green]📸 {name}[/green] → {path}")
                except Exception as e:
                    console.print(f"[red]{name}[/red] → Error: {e}")

        elif command == "eval" and args:
            await self._exec_on_targets(
                lambda page, code=args: page.evaluate(code)
            )

        elif command == "script" and args:
            script_path = Path(args)
            if not script_path.exists():
                # Also check scripts directory
                script_path = Path("scripts") / args
            if script_path.exists():
                js_code = script_path.read_text(encoding="utf-8")
                await self._exec_on_targets(
                    lambda page, code=js_code: page.evaluate(code)
                )
                console.print(f"[green]✓ Script executed: {args}[/green]")
            else:
                console.print(f"[red]Script not found: {args}[/red]")

        elif command == "wait" and args:
            try:
                ms = int(args)
                await asyncio.sleep(ms / 1000)
                console.print(f"[dim]Waited {ms}ms[/dim]")
            except ValueError:
                console.print("[red]Usage: wait <milliseconds>[/red]")

        elif command == "select":
            if args.lower() == "all":
                self.target_profile = None
                console.print("[cyan]Targeting: ALL browsers[/cyan]")
            elif args in self.launcher.list_running():
                self.target_profile = args
                console.print(f"[cyan]Targeting: {args}[/cyan]")
            else:
                console.print(f"[red]Profile '{args}' not running. Available: {', '.join(self.launcher.list_running())}[/red]")

        elif command == "list":
            await self.launcher.display_status()

        elif command == "url":
            pages = self._get_target_pages()
            for name, page in pages:
                console.print(f"[cyan]{name}[/cyan] → {page.url}")

        elif command == "back":
            await self._exec_on_targets(lambda page: page.go_back())

        elif command == "forward":
            await self._exec_on_targets(lambda page: page.go_forward())

        elif command == "reload":
            await self._exec_on_targets(lambda page: page.reload())

        elif command == "close":
            if args:
                try:
                    await self.launcher.close(args)
                except ValueError as e:
                    console.print(f"[red]{e}[/red]")
            else:
                console.print("[red]Usage: close <profile>[/red]")

        else:
            console.print(f"[yellow]Unknown command: {command}. Type 'help' for available commands.[/yellow]")

        return True

    async def run(self):
        """Start the interactive chat loop."""
        console.print(Panel.fit(
            "[bold cyan]🤖 Auto-Browser Chat Interface[/bold cyan]\n"
            "[dim]Type 'help' for commands, 'exit' to quit[/dim]",
            border_style="cyan"
        ))

        target_label = lambda: f"[{self.target_profile or 'all'}]"

        while True:
            try:
                prompt_text = f"🌐 {self.target_profile or 'all'} > "
                cmd = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.session.prompt(prompt_text)
                )
                should_continue = await self.handle_command(cmd)
                if not should_continue:
                    break
            except (KeyboardInterrupt, EOFError):
                break

        console.print("[dim]Chat session ended.[/dim]")
