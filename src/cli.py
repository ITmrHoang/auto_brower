"""
CLI module for Auto-Browser.
Defines all CLI commands using Click.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import AppConfig
from src.profile_manager import ProfileManager
from src.browser_launcher import BrowserLauncher
from src.sync_engine import SyncEngine
from src.chat_interface import ChatInterface
from src.agent import Agent

console = Console()

# Global state
_config: Optional[AppConfig] = None
_profile_mgr: Optional[ProfileManager] = None
_launcher: Optional[BrowserLauncher] = None
_sync_engine: Optional[SyncEngine] = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = AppConfig(base_dir=str(Path(__file__).parent.parent))
    return _config


def get_profile_mgr() -> ProfileManager:
    global _profile_mgr
    if _profile_mgr is None:
        _profile_mgr = ProfileManager(get_config().data_dir)
    return _profile_mgr


def get_launcher() -> BrowserLauncher:
    global _launcher
    if _launcher is None:
        _launcher = BrowserLauncher(get_config())
    return _launcher


def get_sync_engine() -> SyncEngine:
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = SyncEngine(get_launcher())
    return _sync_engine


def run_async(coro):
    """Helper to run async functions from sync click commands."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return loop.run_until_complete(coro)
        else:
            return asyncio.run(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ─── Main CLI Group ──────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0", prog_name="auto-browser")
def cli():
    """🌐 Auto-Browser: CLI Browser Monitoring & Automation"""
    pass


# ─── Profile Commands ────────────────────────────────────────

@cli.group()
def profile():
    """📋 Manage browser profiles"""
    pass


@profile.command("create")
@click.argument("name")
@click.option("--proxy", "-p", default=None, help="Proxy URL (http://... or socks5://...)")
@click.option("--user-agent", "-ua", default=None, help="Custom user agent string")
@click.option("--notes", "-n", default="", help="Profile notes")
def profile_create(name, proxy, user_agent, notes):
    """Create a new browser profile"""
    mgr = get_profile_mgr()
    try:
        p = mgr.create(name, proxy=proxy, user_agent=user_agent, notes=notes)
        console.print(f"[green]✓ Profile '{name}' created[/green]")
        if proxy:
            console.print(f"  [dim]Proxy: {proxy}[/dim]")
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")


@profile.command("list")
def profile_list():
    """List all profiles"""
    get_profile_mgr().display_profiles()


@profile.command("delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this profile?")
def profile_delete(name):
    """Delete a browser profile"""
    try:
        get_profile_mgr().delete(name)
        console.print(f"[green]✓ Profile '{name}' deleted[/green]")
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")


@profile.command("set-proxy")
@click.argument("name")
@click.argument("proxy_url")
def profile_set_proxy(name, proxy_url):
    """Set proxy for a profile"""
    try:
        get_profile_mgr().set_proxy(name, proxy_url)
        console.print(f"[green]✓ Proxy set for '{name}': {proxy_url}[/green]")
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")


@profile.command("info")
@click.argument("name")
def profile_info(name):
    """Show profile details"""
    p = get_profile_mgr().get(name)
    if p:
        import json
        console.print_json(json.dumps(p, indent=2, ensure_ascii=False))
    else:
        console.print(f"[red]Profile '{name}' not found[/red]")


# ─── Launch Commands ──────────────────────────────────────────

@cli.command()
@click.argument("profiles", nargs=-1, required=False)
@click.option("--all", "launch_all", is_flag=True, help="Launch all profiles")
@click.option("--headless", is_flag=True, help="Run in headless mode")
@click.option("--width", "-w", default=800, help="Window width")
@click.option("--height", "-h", default=600, help="Window height")
def launch(profiles, launch_all, headless, width, height):
    """🚀 Launch browser(s) with a profile"""
    mgr = get_profile_mgr()

    if launch_all:
        profiles = [p["name"] for p in mgr.list_profiles()]
    elif not profiles:
        console.print("[red]Specify profile name(s) or use --all[/red]")
        return

    async def _launch():
        launcher = get_launcher()
        for name in profiles:
            pc = mgr.get(name)
            if not pc:
                # Auto-create profile if needed
                console.print(f"[yellow]Profile '{name}' not found, creating...[/yellow]")
                pc = mgr.create(name)
            try:
                await launcher.launch(
                    name, pc,
                    headless=headless,
                    window_size=(width, height)
                )
            except Exception as e:
                console.print(f"[red]✗ Failed to launch '{name}': {e}[/red]")

        # Keep running until all browsers close
        console.print("\n[dim]Press Ctrl+C to exit...[/dim]")
        try:
            while launcher.list_running():
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await launcher.shutdown()

    run_async(_launch())


# ─── Status Command ───────────────────────────────────────────

@cli.command()
def status():
    """📊 Show running browsers status"""
    run_async(get_launcher().display_status())


# ─── Close Command ────────────────────────────────────────────

@cli.command("close")
@click.argument("profile", required=False)
@click.option("--all", "close_all", is_flag=True, help="Close all browsers")
def close_browser(profile, close_all):
    """🔴 Close browser(s)"""
    async def _close():
        launcher = get_launcher()
        if close_all:
            await launcher.close_all()
        elif profile:
            try:
                await launcher.close(profile)
            except ValueError as e:
                console.print(f"[red]✗ {e}[/red]")
        else:
            console.print("[red]Specify profile name or use --all[/red]")

    run_async(_close())


# ─── Sync Commands ────────────────────────────────────────────

@cli.group()
def sync():
    """🔄 Browser synchronization"""
    pass


@sync.command("start")
@click.option("--root", "-r", required=True, help="Root browser profile")
@click.option("--followers", "-f", multiple=True, help="Follower profiles (can specify multiple)")
def sync_start(root, followers):
    """Start syncing from root to followers"""
    async def _sync():
        launcher = get_launcher()
        engine = get_sync_engine()

        # Verify all browsers are running
        running = launcher.list_running()
        if root not in running:
            console.print(f"[red]Root browser '{root}' is not running. Launch it first.[/red]")
            return
        for f in followers:
            if f not in running:
                console.print(f"[red]Follower browser '{f}' is not running. Launch it first.[/red]")
                return

        engine.set_root(root)
        for f in followers:
            engine.add_follower(f)

        await engine.start()

        console.print("\n[dim]Sync active. Press Ctrl+C to stop...[/dim]")
        try:
            while engine.is_running:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            await engine.stop()

    run_async(_sync())


@sync.command("stop")
def sync_stop():
    """Stop syncing"""
    run_async(get_sync_engine().stop())


@sync.command("status")
def sync_status():
    """Show sync status"""
    get_sync_engine().display_status()


# ─── Chat Command ─────────────────────────────────────────────

@cli.command()
@click.option("--agent", "use_agent", is_flag=True, help="Enable AI agent mode")
@click.option("--api-key", default=None, help="AI API key (for agent mode)")
def chat(use_agent, api_key):
    """💬 Interactive chat interface to control browsers"""
    async def _chat():
        launcher = get_launcher()

        if not launcher.list_running():
            console.print("[yellow]No browsers running. Launching with chat...[/yellow]")

        chat_iface = ChatInterface(launcher, get_sync_engine())

        if use_agent:
            agent = Agent(api_key=api_key)
            console.print("[cyan]🤖 Agent mode enabled (Vietnamese/English)[/cyan]")

            # Wrap chat to support agent parsing
            original_handler = chat_iface.handle_command

            async def agent_handler(cmd):
                # Try direct command first
                parts = cmd.strip().split()
                known = {"goto", "click", "type", "fill", "press", "scroll",
                         "screenshot", "eval", "script", "wait", "select",
                         "list", "url", "back", "forward", "reload", "close",
                         "help", "exit", "quit", "q"}
                if parts and parts[0].lower() in known:
                    return await original_handler(cmd)

                # Try agent parsing
                parsed = await agent.process(cmd)
                if parsed:
                    return await original_handler(parsed)
                return True

            chat_iface.handle_command = agent_handler

        await chat_iface.run()

    run_async(_chat())


# ─── Run Script Command ───────────────────────────────────────

@cli.command("run")
@click.argument("script_file")
@click.option("--target", "-t", default=None, help="Target profile (default: all)")
def run_script(script_file, target):
    """📜 Run a JavaScript file on browser(s)"""
    script_path = Path(script_file)
    if not script_path.exists():
        script_path = Path("scripts") / script_file
    if not script_path.exists():
        console.print(f"[red]Script not found: {script_file}[/red]")
        return

    js_code = script_path.read_text(encoding="utf-8")

    async def _run():
        launcher = get_launcher()
        targets = [target] if target else launcher.list_running()
        for name in targets:
            inst = launcher.get_instance(name)
            if inst and inst.active_page:
                try:
                    result = await inst.active_page.evaluate(js_code)
                    console.print(f"[green]✓ {name}[/green]: {result}")
                except Exception as e:
                    console.print(f"[red]✗ {name}[/red]: {e}")

    run_async(_run())


# ─── Interactive Mode (launch + chat) ─────────────────────────

@cli.command("interactive")
@click.argument("profiles", nargs=-1, required=True)
@click.option("--proxy", "-p", default=None, help="Proxy URL for all profiles")
@click.option("--agent", "use_agent", is_flag=True, help="Enable AI agent mode")
@click.option("--sync-root", default=None, help="Set root for sync")
def interactive(profiles, proxy, use_agent, sync_root):
    """🎮 Launch browsers and enter chat mode"""
    async def _interactive():
        mgr = get_profile_mgr()
        launcher = get_launcher()

        # Launch all profiles
        for name in profiles:
            pc = mgr.get(name)
            if not pc:
                pc = mgr.create(name, proxy=proxy)
            elif proxy:
                mgr.set_proxy(name, proxy)
                pc = mgr.get(name)
            try:
                await launcher.launch(name, pc)
            except Exception as e:
                console.print(f"[red]✗ Failed to launch '{name}': {e}[/red]")

        # Set up sync if requested
        if sync_root and sync_root in profiles:
            engine = get_sync_engine()
            engine.set_root(sync_root)
            for name in profiles:
                if name != sync_root:
                    engine.add_follower(name)
            await engine.start()

        # Start chat
        chat_iface = ChatInterface(launcher, get_sync_engine())

        if use_agent:
            agent = Agent()
            original_handler = chat_iface.handle_command

            async def agent_handler(cmd):
                parts = cmd.strip().split()
                known = {"goto", "click", "type", "fill", "press", "scroll",
                         "screenshot", "eval", "script", "wait", "select",
                         "list", "url", "back", "forward", "reload", "close",
                         "help", "exit", "quit", "q"}
                if parts and parts[0].lower() in known:
                    return await original_handler(cmd)
                parsed = await agent.process(cmd)
                if parsed:
                    return await original_handler(parsed)
                return True

            chat_iface.handle_command = agent_handler

        await chat_iface.run()
        await launcher.shutdown()



# --- GUI Command ---

@cli.command("gui")
def start_gui():
    """🖥️ Start the Desktop GUI"""
    import threading
    import uvicorn
    import webview
    import time

    # Setup paths
    base_dir = Path(__file__).parent.parent
    gui_dir = base_dir / "gui"
    html_file = gui_dir / "index.html"
    
    if not html_file.exists():
        console.print(f"[red]GUI files not found at {html_file}[/red]")
        return
        
    console.print("[cyan]Starting Auto-Browser Desktop...[/cyan]")

    # Start FastAPI in background
    def run_server():
        # Hide uvicorn access logs
        import logging
        log = logging.getLogger("uvicorn.access")
        log.setLevel(logging.WARNING)
        
        from src.gui_app import app
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait a sec for server to bind
    time.sleep(1)

    # Launch PyWebView window
    window = webview.create_window(
        "Auto-Browser", 
        url=f"file:///{str(html_file.absolute()).replace(os.sep, '/')}",
        width=1000, 
        height=700,
        resizable=True,
        background_color="#0f172a"
    )
    
    console.print("[dim]Close the GUI window to exit.[/dim]")
    webview.start()
    
    # Upon window close, attempt to shutdown browsers gracefully
    launcher = get_launcher()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(launcher.shutdown())
        else:
            loop.run_until_complete(launcher.shutdown())
    except Exception:
        pass
    
    console.print("[green]GUI closed.[/green]")
    os._exit(0)  # Force exit to kill uvicorn thread


if __name__ == "__main__":
    cli()
