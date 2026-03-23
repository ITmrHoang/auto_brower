"""
Sync Engine for Auto-Browser.
Cơ chế đồng bộ (Synchronization Mechanism):
1. Root Profile: Trình duyệt đóng vai trò "Máy chủ phát lệnh" (Nơi user thực tết thao tác).
2. Followers: Các trình duyệt đóng vai trò "Máy khách nhận lệnh" (Nhận và tái hiện lại hành động).
3. Cách hoạt động: 
   - Tiêm mã JS (CAPTURE_EVENTS_JS) vào trang Root để lắng nghe mọi sự kiện DOM (click, scroll, input...).
   - Lưu trữ các sự kiện đó vào một mảng tạm `window.__autoBrowserEvents` bên trong môi trường web của Root.
   - Python Backend liên tục "gặt" (poll) dữ liệu từ mảng này (mỗi 0.3s) thông qua việc đánh giá mã JS `FLUSH_EVENTS_JS`.
   - Với mỗi sự kiện gặt được, Python phân tách và gọi lại API của Playwright để tái hiện lại hành vi vật lý đó
     (vd: `page.click()`, `page.fill()`) lên toàn bộ các trình duyệt Followers cùng một lúc.
"""

import asyncio
import json
from typing import Optional, List, Set

from rich.console import Console

console = Console()


# JavaScript to inject into the root browser to capture user actions
CAPTURE_EVENTS_JS = """
(function() {
    if (window.__autoBrowserSyncActive) return;
    window.__autoBrowserSyncActive = true;
    window.__autoBrowserEvents = [];

    // Capture clicks
    document.addEventListener('click', (e) => {
        const path = getSelector(e.target);
        window.__autoBrowserEvents.push({
            type: 'click',
            selector: path,
            x: e.clientX,
            y: e.clientY,
            timestamp: Date.now()
        });
    }, true);

    // Capture input/typing
    document.addEventListener('input', (e) => {
        const path = getSelector(e.target);
        window.__autoBrowserEvents.push({
            type: 'input',
            selector: path,
            value: e.target.value,
            timestamp: Date.now()
        });
    }, true);

    // Capture scroll
    let scrollTimer = null;
    document.addEventListener('scroll', (e) => {
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(() => {
            window.__autoBrowserEvents.push({
                type: 'scroll',
                scrollX: window.scrollX,
                scrollY: window.scrollY,
                timestamp: Date.now()
            });
        }, 100);
    }, true);

    // Capture key presses (for shortcuts)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === 'Tab' || e.key === 'Escape') {
            window.__autoBrowserEvents.push({
                type: 'keypress',
                key: e.key,
                timestamp: Date.now()
            });
        }
    }, true);

    // Helper: generate a CSS selector for an element
    function getSelector(el) {
        if (!el || el === document || el === document.body) return 'body';
        if (el.id) return '#' + CSS.escape(el.id);
        if (el === document.documentElement) return 'html';

        const path = [];
        let current = el;
        while (current && current !== document.body) {
            let selector = current.tagName.toLowerCase();
            if (current.id) {
                selector = '#' + CSS.escape(current.id);
                path.unshift(selector);
                break;
            }
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\\s+/).filter(c => c.length > 0 && !c.includes(':'));
                if (classes.length > 0) {
                    selector += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
                }
            }
            // Add nth-child for disambiguation
            const parent = current.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
                if (siblings.length > 1) {
                    const index = siblings.indexOf(current) + 1;
                    selector += ':nth-child(' + index + ')';
                }
            }
            path.unshift(selector);
            current = current.parentElement;
        }
        return path.join(' > ');
    }

    // Function to flush events
    window.__autoBrowserFlushEvents = function() {
        const events = window.__autoBrowserEvents.splice(0);
        return JSON.stringify(events);
    };
})();
"""

# JavaScript to poll and flush events
FLUSH_EVENTS_JS = """
(() => {
    if (typeof window.__autoBrowserFlushEvents === 'function') {
        return window.__autoBrowserFlushEvents();
    }
    return '[]';
})()
"""


class SyncEngine:
    """Captures actions from a root browser and replays them to followers."""

    def __init__(self, browser_launcher):
        self.launcher = browser_launcher
        self.root_profile: Optional[str] = None
        self.followers: Set[str] = set()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._poll_interval = 0.3  # seconds
        
        # Recording mode
        self.record_mode = False
        self.recorded_events = []

    def get_recorded_events(self):
        return self.recorded_events
        
    def clear_recorded_events(self):
        self.recorded_events = []

    def set_root(self, profile_name: str):
        """Set the root browser (source of actions)."""
        if profile_name not in self.launcher.instances:
            raise ValueError(f"Browser '{profile_name}' is not running")
        self.root_profile = profile_name
        console.print(f"[cyan]👑 Root browser set to:[/cyan] [bold]{profile_name}[/bold]")

    def add_follower(self, profile_name: str):
        """Add a follower browser."""
        if profile_name not in self.launcher.instances:
            raise ValueError(f"Browser '{profile_name}' is not running")
        if profile_name == self.root_profile:
            raise ValueError("Cannot add root browser as follower")
        self.followers.add(profile_name)
        console.print(f"[green]➕ Added follower:[/green] [bold]{profile_name}[/bold]")

    def remove_follower(self, profile_name: str):
        """Remove a follower browser."""
        self.followers.discard(profile_name)
        console.print(f"[red]➖ Removed follower:[/red] [bold]{profile_name}[/bold]")

    async def start(self):
        """Start syncing actions from root to followers or start recording."""
        if not self.root_profile:
            raise ValueError("No root browser set")
        if not self.followers and not self.record_mode:
            raise ValueError("No follower browsers added and not in record mode")

        self._running = True

        # Inject capture script into root browser
        root_instance = self.launcher.get_instance(self.root_profile)
        if not root_instance or not root_instance.active_page:
            raise ValueError("Root browser has no active page")

        # Tiêm kịch bản bắt sự kiện (Gián điệp JS) vào trình duyệt Root
        root_page = root_instance.active_page
        await root_page.evaluate(CAPTURE_EVENTS_JS)

        # Lắng nghe sự kiện "load" (Khi Root điều hướng sang trang khác hoặc F5):
        # Lúc này trang bị reset nên Gián điệp JS cũ sẽ bị xóa sổ theo.
        # Ta cần đăng ký một hàm callback (lambda) để tiêm lại JS ngay khi trang mới tải xong.
        # Lưu ý: Hàm `on` của Playwright nhận một hàm đồng bộ bình thường.
        # Dùng `asyncio.ensure_future()` để biến việc tiêm lại (hàm bất đồng bộ `_reinject_capture`)
        # thành một công việc chạy ở chế độ nền (Background task) nhằm không làm chặn (blocking) tiến trình chính.
        root_page.on("load", lambda: asyncio.ensure_future(self._reinject_capture(root_page)))

        # Start the sync loop
        self._task = asyncio.create_task(self._sync_loop())
        console.print(f"[green]▶ Sync started:[/green] {self.root_profile} → {', '.join(self.followers)}")

    async def _reinject_capture(self, page):
        """Re-inject capture script after navigation."""
        try:
            await page.evaluate(CAPTURE_EVENTS_JS)
        except Exception:
            pass

    async def _sync_loop(self):
        """Main sync loop: poll root for events, replay on followers."""
        last_url = None

        while self._running:
            try:
                root_instance = self.launcher.get_instance(self.root_profile)
                if not root_instance or not root_instance.active_page:
                    await asyncio.sleep(self._poll_interval)
                    continue

                root_page = root_instance.active_page

                # 1. ĐỒNG BỘ ĐIỀU HƯỚNG MẠNG (URL Syncing)
                # Kỹ thuật: So sánh URL hiện tại của Root với chu kỳ trước đó.
                # Nếu URL lọt vào trang mới, bắt tất cả Client (Followers) chuyển hướng .goto(url) đi theo ngay lập tức.
                current_url = root_page.url
                if last_url and current_url != last_url:
                    await self._replay_navigation(current_url)
                last_url = current_url

                # 2. XẢ THÙNG CHỨA SỰ KIỆN TỪ ROOT (Flushing Events)
                # Ở đây chúng ta đâm mã FLUSH_EVENTS_JS vào Root.
                # Đoạn mã này sẽ lấy sạch dữ liệu từ mảng `window.__autoBrowserEvents` và đổ ra dạng chuỗi JSON,
                # đồng thời dọn dẹp mảng đó trên trình duyệt để lấy chỗ lưu thao tác tiếp theo.
                try:
                    events_json = await root_page.evaluate(FLUSH_EVENTS_JS)
                    events = json.loads(events_json) if events_json else []
                except Exception:
                    events = []

                # 3. TÁI LẬP HÀNH ĐỘNG LÊN TOÀN BỘ CLIENT (Replay Events Dispatcher)
                # Với từng sự kiện lấy được (click, input...), ném nó qua hàm _replay_event
                # để tái hiện lại nó trên tất cả các trình duyệt con.
                for event in events:
                    if self.record_mode:
                        self.recorded_events.append(event)
                    else:
                        await self._replay_event(event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                console.print(f"[dim red]Sync error: {e}[/dim red]")

            await asyncio.sleep(self._poll_interval)

    async def _replay_navigation(self, url: str):
        """Navigate all followers to the same URL."""
        tasks = []
        for fname in list(self.followers):
            inst = self.launcher.get_instance(fname)
            if inst and inst.active_page:
                tasks.append(self._safe_goto(inst.active_page, url))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_goto(self, page, url):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass

    async def _replay_event(self, event: dict):
        """Phân phối 1 hành động của người dùng (từ Root) lên mọi Follower (Clients)."""
        event_type = event.get("type")
        tasks = []

        # Lặp qua tất cả Follower hiện tại và thu thập các Task tái lập hành động.
        for fname in list(self.followers):
            inst = self.launcher.get_instance(fname)
            if not inst or not inst.active_page:
                continue
            page = inst.active_page
            # Gắn lệnh bắt trang Client tái lập chuỗi event vào trong một Task.
            tasks.append(self._replay_single(page, event))

        # Sử dụng asyncio.gather để phóng đồng loạt các tác vụ này (chạy song song).
        # Tức là nếu có 10 clients, hành động Click sẽ diễn ra gần như cùng 1 lúc trên cả 10 tabs thay vì đợi tuần tự.
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _replay_single(self, page, event: dict):
        """Replay a single event on a single page."""
        try:
            event_type = event["type"]
            selector = event.get("selector")

            if event_type == "click":
                if selector:
                    try:
                        await page.click(selector, timeout=3000)
                    except Exception:
                        # Fallback: click by coordinates
                        x, y = event.get("x", 0), event.get("y", 0)
                        await page.mouse.click(x, y)

            elif event_type == "input":
                if selector:
                    await page.fill(selector, event.get("value", ""), timeout=3000)

            elif event_type == "scroll":
                sx, sy = event.get("scrollX", 0), event.get("scrollY", 0)
                await page.evaluate(f"window.scrollTo({sx}, {sy})")

            elif event_type == "keypress":
                key = event.get("key", "")
                await page.keyboard.press(key)

        except Exception:
            pass  # Silently skip failed replays

    async def stop(self):
        """Stop syncing."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        console.print("[red]⏹ Sync stopped[/red]")

    @property
    def is_running(self) -> bool:
        return self._running

    def display_status(self):
        """Display sync status."""
        if not self._running:
            console.print("[yellow]Sync is not active[/yellow]")
            return
        console.print(f"[green]▶ Sync active[/green]")
        console.print(f"  [cyan]Root:[/cyan] {self.root_profile}")
        console.print(f"  [cyan]Followers:[/cyan] {', '.join(self.followers) or 'none'}")
