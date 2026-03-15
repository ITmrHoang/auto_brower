"""
FastAPI Backend for the Auto-Browser Desktop GUI.
Provides REST endpoints for the frontend to interact with the core CLI logic.
"""

import asyncio
import os
import json
from pathlib import Path
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import AppConfig
from .profile_manager import ProfileManager
from .browser_launcher import BrowserLauncher
from .sync_engine import SyncEngine


app = FastAPI(title="Auto-Browser GUI API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (will be initialized on startup)
config: AppConfig = None
profile_mgr: ProfileManager = None
launcher: BrowserLauncher = None
sync_engine: SyncEngine = None


@app.on_event("startup")
async def startup_event():
    global config, profile_mgr, launcher, sync_engine
    base_dir = str(Path(__file__).parent.parent)
    config = AppConfig(base_dir=base_dir)
    profile_mgr = ProfileManager(config.data_dir)
    launcher = BrowserLauncher(config)
    sync_engine = SyncEngine(launcher)


@app.on_event("shutdown")
async def shutdown_event():
    if launcher:
        await launcher.shutdown()


# --- Models ---

class ProfileCreateReq(BaseModel):
    name: str
    proxy: Optional[str] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    user_agent: Optional[str] = None
    notes: Optional[str] = ""

class ProfileUpdateReq(BaseModel):
    proxy: Optional[str] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    notes: Optional[str] = None

class LaunchReq(BaseModel):
    profile_name: str
    headless: bool = False


class ScriptRunReq(BaseModel):
    script_name: str
    target_profiles: List[str]


class SyncStartReq(BaseModel):
    root_profile: str
    followers: List[str]


class RecordStartReq(BaseModel):
    root_profile: str


class RecordStopReq(BaseModel):
    filename: str


# --- API Routes ---

@app.get("/api/profiles")
def get_profiles():
    profiles = profile_mgr.list_profiles()
    # Add status info
    running = launcher.list_running() if launcher else []
    for p in profiles:
        p["status"] = "running" if p["name"] in running else "stopped"
    return profiles


@app.post("/api/profiles")
def create_profile(req: ProfileCreateReq):
    try:
        p = profile_mgr.create(
            req.name, proxy=req.proxy, 
            proxy_username=req.proxy_username,
            proxy_password=req.proxy_password,
            user_agent=req.user_agent, notes=req.notes
        )
        return p
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/profiles/{name}")
def update_profile(name: str, req: ProfileUpdateReq):
    try:
        updates = {k: v for k, v in req.dict().items() if v is not None}
        if updates:
            p = profile_mgr.update(name, **updates)
            return p
        return profile_mgr.get(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/profiles/{name}")
def delete_profile(name: str):
    try:
        # Close if running
        if launcher and name in launcher.list_running():
            asyncio.create_task(launcher.close(name))
        
        profile_mgr.delete(name)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/browser/launch")
async def launch_browser(req: LaunchReq, background_tasks: BackgroundTasks):
    p = profile_mgr.get(req.profile_name)
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if req.profile_name in launcher.list_running():
        raise HTTPException(status_code=400, detail="Browser already running")

    # Add to background to resolve API call quickly
    async def _do_launch():
        try:
            await launcher.launch(req.profile_name, p, headless=req.headless)
        except Exception as e:
            print(f"Launch error: {e}")
            
    background_tasks.add_task(_do_launch)
    return {"status": "launching"}


@app.post("/api/browser/close")
async def close_browser(req: dict = Body(...)):
    name = req.get("profile_name")
    if not name:
        raise HTTPException(status_code=400, detail="profile_name required")
    
    if name not in launcher.list_running():
        raise HTTPException(status_code=400, detail="Browser not running")
        
    await launcher.close(name)
    return {"status": "success"}


@app.get("/api/browser/status")
def get_browser_status():
    if not launcher:
        return []
    
    running = []
    for name, inst in launcher.instances.items():
        running.append({
            "name": name,
            "pages": len(inst.pages),
            "launched_at": inst.launched_at.isoformat()
        })
    return running


@app.get("/api/scripts")
def get_scripts():
    scripts = []
    if config.scripts_dir.exists():
        for item in config.scripts_dir.iterdir():
            if item.suffix == ".js":
                scripts.append({
                    "name": item.name,
                    "path": str(item)
                })
    return scripts


@app.post("/api/scripts/run")
async def run_script(req: ScriptRunReq, background_tasks: BackgroundTasks):
    script_path = config.scripts_dir / req.script_name
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Script not found")
        
    js_code = script_path.read_text(encoding="utf-8")
    
    async def _run():
        for name in req.target_profiles:
            inst = launcher.get_instance(name)
            if inst and inst.active_page:
                try:
                    await inst.active_page.evaluate(js_code)
                except Exception as e:
                    print(f"Script run error on {name}: {e}")
                    
    background_tasks.add_task(_run)
    return {"status": "running"}


# Sync & Record routes
@app.post("/api/sync/start")
async def start_sync(req: SyncStartReq):
    try:
        if sync_engine.is_running:
            await sync_engine.stop()
            
        sync_engine.set_root(req.root_profile)
        for f in req.followers:
            sync_engine.add_follower(f)
            
        # Ensure we are not in record mode
        sync_engine.record_mode = False
        await sync_engine.start()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sync/stop")
async def stop_sync():
    await sync_engine.stop()
    return {"status": "success"}


@app.post("/api/record/start")
async def start_record(req: RecordStartReq):
    try:
        if sync_engine.is_running:
            await sync_engine.stop()
            
        sync_engine.set_root(req.root_profile)
        sync_engine.followers.clear()  # No followers during pure record
        sync_engine.record_mode = True
        await sync_engine.start()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/record/stop")
async def stop_record(req: RecordStopReq):
    if not sync_engine.is_running or not getattr(sync_engine, 'record_mode', False):
        raise HTTPException(status_code=400, detail="Not recording")
        
    await sync_engine.stop()
    
    # Save recording to script file
    events = sync_engine.get_recorded_events()
    if not events:
        return {"status": "no events recorded"}
        
    filename = req.filename
    if not filename.endswith(".js"):
        filename += ".js"
        
    script_path = config.scripts_dir / filename
    
    # Generate Playwright/browser JS script from events
    js_content = generate_script_from_events(events)
    script_path.write_text(js_content, encoding="utf-8")
    
    # Clear events
    sync_engine.clear_recorded_events()
    
    return {"status": "success", "file": filename, "events": len(events)}


def generate_script_from_events(events):
    """Convert recorded events into an executable JS script inside the browser context."""
    lines = ["// Auto-generated recorded script", "async function run() {"]
    
    for ev in events:
        t = ev.get("type")
        s = ev.get("selector")
        
        # Add a small delay between actions for safety if timestamp exists
        # In a real impl, we'd calculate deltas. Here a fixed 500ms delay:
        lines.append("  await new Promise(r => setTimeout(r, 500));")
        
        if t == "click" and s:
            lines.append(f"  const el_{len(lines)} = document.querySelector(`{s}`);")
            lines.append(f"  if (el_{len(lines)}) el_{len(lines)}.click();")
        elif t == "input" and s:
            val = ev.get("value", "").replace('`', '\\`').replace('$', '\\$')
            lines.append(f"  const el_{len(lines)} = document.querySelector(`{s}`);")
            lines.append(f"  if (el_{len(lines)}) {{ el_{len(lines)}.value = `{val}`; el_{len(lines)}.dispatchEvent(new Event('input', {{bubbles: true}})); el_{len(lines)}.dispatchEvent(new Event('change', {{bubbles: true}})); }}")
        elif t == "scroll":
            x, y = ev.get("scrollX", 0), ev.get("scrollY", 0)
            lines.append(f"  window.scrollTo({x}, {y});")
            
    lines.append("}")
    lines.append("run().catch(console.error);")
    return "\n".join(lines)


@app.get("/api/sync/status")
def get_sync_status():
    return {
        "running": sync_engine.is_running if sync_engine else False,
        "root": sync_engine.root_profile if sync_engine else None,
        "followers": list(sync_engine.followers) if sync_engine else [],
        "record_mode": getattr(sync_engine, 'record_mode', False) if sync_engine else False
    }
