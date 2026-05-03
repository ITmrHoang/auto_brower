"""
Fingerprint Generator for Auto-Browser.
Generates random but consistent browser fingerprints per profile.
"""

import random
import hashlib
import json
import requests
from typing import Optional


# Độ phân giải Màn hình PC/Laptop phổ thông
PC_SCREENS = [
    (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
    (1600, 900), (2560, 1440), (1280, 800), (1680, 1050),
    (1920, 1200), (2560, 1600),
]
SCREEN_RESOLUTIONS = PC_SCREENS

# Danh sách Timezone dự phòng
TIMEZONES = [
    "America/New_York", "America/Chicago", "America/Denver",
    "America/Los_Angeles", "Europe/London", "Europe/Paris",
    "Europe/Berlin", "Asia/Tokyo", "Asia/Shanghai",
    "Australia/Sydney", "Asia/Ho_Chi_Minh",
]

# ===== USER AGENTS PHÂN LOẠI THEO NỀN TẢNG =====
# Windows Chrome & Edge
WIN_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

# macOS Chrome & Safari
MAC_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# Linux Chrome
LINUX_USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]
# Gộp toàn bộ UA
USER_AGENTS = WIN_USER_AGENTS + MAC_USER_AGENTS + LINUX_USER_AGENTS

# Bộ Ánh xạ Hệ Sinh Thái Đồng bộ (Platform -> Screen)
DEVICE_ECOSYSTEMS = [
    {"weight": 60, "ua_list": WIN_USER_AGENTS, "platforms": ["Win32"], "screens": PC_SCREENS},
    {"weight": 35, "ua_list": MAC_USER_AGENTS, "platforms": ["MacIntel"], "screens": PC_SCREENS},
    {"weight": 5, "ua_list": LINUX_USER_AGENTS, "platforms": ["Linux x86_64"], "screens": PC_SCREENS},
]

# Languages (Mở rộng thêm nhiều khu vực ngôn ngữ)
LANGUAGE_SETS = [
    # Tiếng Anh
    ["en-US", "en"],
    ["en-GB", "en-US", "en"],
    ["en-CA", "en-US", "en"],
    ["en-AU", "en-GB", "en"],
    
    # Tiếng Châu Á
    ["vi-VN", "vi", "en-US", "en"],
    ["ja-JP", "ja", "en-US", "en"],
    ["ko-KR", "ko", "en-US", "en"],
    ["zh-CN", "zh", "en-US", "en"],
    ["zh-TW", "zh", "en-US", "en"],
    ["th-TH", "th", "en-US", "en"],
    ["id-ID", "id", "en-US", "en"],
    
    # Tiếng Châu Âu
    ["fr-FR", "fr", "en-US", "en"],
    ["de-DE", "de", "en-US", "en"],
    ["es-ES", "es", "en-US", "en"],
    ["it-IT", "it", "en-US", "en"],
    ["ru-RU", "ru", "en-US", "en"],
    ["pt-BR", "pt", "en-US", "en"],
    ["nl-NL", "nl", "en-US", "en"],
]


def generate_fingerprint(seed: Optional[str] = None, proxy: Optional[str] = None, custom_user_agent: Optional[str] = None) -> dict:
    """
    Generate a random but deterministic fingerprint.
    If seed is provided, the same seed always produces the same fingerprint.
    If proxy is provided, it tries to detect correct timezone and language from that IP.
    """
    if seed:
        rng = random.Random(hashlib.md5(seed.encode()).hexdigest())
    else:
        rng = random.Random()

    # Mặc định lấy ngẫu nhiên nếu dò timezone thất bại
    timezone = rng.choice(TIMEZONES)
    languages = rng.choice(LANGUAGE_SETS)
    
    # Tọa độ mặc định (Mỹ) nếu dò thất bại, thay vì 0,0 giữa biển
    latitude = 40.7128 + (rng.random() - 0.5) * 0.1
    longitude = -74.0060 + (rng.random() - 0.5) * 0.1
    
    # Public IP thực tế của Proxy (dùng giả mạo WebRTC)
    public_ip: Optional[str] = None
    
    # Random nhiễu hạt ảo cho Cánvas và Font (Cố định theo Seed)
    canvas_noise_r = rng.randint(-2, 2)
    canvas_noise_g = rng.randint(-2, 2)
    canvas_noise_b = rng.randint(-2, 2)
    font_noise = rng.random() * 0.2 - 0.1 # Nảy lệch từ -0.1px tới +0.1px
    
    # Random số lượng thiết bị vật lý (Microphone, Loa, Webcam)
    media_audio_in = rng.choice([1, 2])
    media_audio_out = rng.choice([1, 2, 3])
    media_video_in = rng.choice([0, 1])
    
    # Auto-detect Location/Timezone via IP API
    try:
        proxies = None
        if proxy:
            # Handle format like http://user:pass@ip:port correctly
            proxies = {
                "http": proxy,
                "https": proxy
            }
        
        # Tiết kiệm thời gian, tăng timeout lên 5s cho proxy chậm
        resp = requests.get("http://ip-api.com/json/", proxies=proxies, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                detected_tz = data.get("timezone")
                detected_country = data.get("countryCode")
                
                if data.get("lat") is not None:
                    latitude = float(data.get("lat"))
                    longitude = float(data.get("lon"))
                    
                if data.get("query"):
                    public_ip = data.get("query")
                    
                if detected_tz:
                    timezone = detected_tz
                
                if detected_country:
                    # Chế ra một Locale dựa vào Country (Ví dụ VN -> vi-VN)
                    loc = f"{detected_country.lower()}-{detected_country.upper()}"
                    languages = [loc, detected_country.lower(), "en-US", "en"]
    except Exception:
        pass # Fallback về random bình thường nếu mạng lỗi/proxy chết

    # CHỌN HỆ SINH THÁI THIẾT BỊ ĐỒNG BỘ (UA + Platform + Screen cùng 1 nền tảng PC)
    if custom_user_agent:
        # Nếu Người dùng chỉ định UserAgent cụ thể, dò tìm nền tảng theo nội dung của chuỗi đó
        ua = custom_user_agent
        if "Mac OS X" in ua:
            match_platform = "MacIntel"
        elif "Linux" in ua:
            match_platform = "Linux x86_64"
        else:
            match_platform = "Win32"
        screen = rng.choice(PC_SCREENS)
    else:
        # Random theo Tỉ trọng Thị Trường (Trọng số cho Windows cao nhất)
        pc_ecosystems = DEVICE_ECOSYSTEMS
        weights = [e["weight"] for e in pc_ecosystems]
        eco = rng.choices(pc_ecosystems, weights=weights, k=1)[0]
        ua = rng.choice(eco["ua_list"])
        match_platform = rng.choice(eco["platforms"])
        screen = rng.choice(eco["screens"])

    fingerprint = {
        "screen_width": screen[0],
        "screen_height": screen[1],
        "color_depth": rng.choice([24, 32]),
        "timezone": timezone,
        "platform": match_platform,
        "user_agent": ua,
        "languages": languages,
        "do_not_track": rng.choice([None, "1"]),
        "max_touch_points": 0,
        "latitude": latitude,
        "longitude": longitude,
        "public_ip": public_ip,
        "canvas_noise": {"r": canvas_noise_r, "g": canvas_noise_g, "b": canvas_noise_b},
        "font_noise": font_noise,
        "media_devices": {"audio_in": media_audio_in, "audio_out": media_audio_out, "video_in": media_video_in}
    }

    return fingerprint


def fingerprint_to_stealth_script(fp: dict) -> str:
    """Convert a fingerprint to JavaScript injection script."""
    fp_json = json.dumps(fp)
    return f"""
(function() {{
    const fp = {fp_json};

    // Override user agent
    Object.defineProperty(navigator, 'userAgent', {{ get: () => fp.user_agent }});
    Object.defineProperty(navigator, 'appVersion', {{ get: () => fp.user_agent.replace('Mozilla/', '') }});

    // Override platform
    Object.defineProperty(navigator, 'platform', {{ get: () => fp.platform }});

    // Override languages
    Object.defineProperty(navigator, 'languages', {{ get: () => fp.languages }});
    Object.defineProperty(navigator, 'language', {{ get: () => fp.languages[0] }});

    // Override userAgentData (Client Hints)
    let chPlatform = "Windows";
    if (fp.platform.includes("Mac")) chPlatform = "macOS";
    else if (fp.platform.includes("Linux")) chPlatform = "Linux";

    Object.defineProperty(navigator, 'userAgentData', {{
        get: () => ({{
            brands: [
                {{ brand: "Not_A Brand", version: "8" }},
                {{ brand: "Chromium", version: "120" }},
                {{ brand: "Google Chrome", version: "120" }}
            ],
            mobile: false,
            platform: chPlatform,
            getHighEntropyValues: async (hints) => {{
                return {{
                    architecture: "x86",
                    bitness: "64",
                    brands: [
                        {{ brand: "Not_A Brand", version: "8" }},
                        {{ brand: "Chromium", version: "120" }},
                        {{ brand: "Google Chrome", version: "120" }}
                    ],
                    mobile: false,
                    model: "",
                    platform: chPlatform,
                    platformVersion: "10.0.0",
                    uaFullVersion: "120.0.6099.109"
                }};
            }}
        }})
    }});

    // Override screen
    Object.defineProperty(screen, 'width', {{ get: () => fp.screen_width }});
    Object.defineProperty(screen, 'height', {{ get: () => fp.screen_height }});
    Object.defineProperty(screen, 'availWidth', {{ get: () => fp.screen_width }});
    // Taskbar offset randomization: Random lệch khung trình duyệt 40px - 70px
    const randomOffset = 40 + Math.floor(Math.random() * 30);
    Object.defineProperty(screen, 'availHeight', {{ get: () => fp.screen_height - randomOffset }});
    
    // colorDepth: Độ sâu màu của màn hình (thường là 24-bit hoặc 32-bit trên PC hiện đại).
    // Anti-bot dùng nó để kiểm tra tính Logic: Nếu Màn hình to (Ví dụ 4K) mà Màu sắc lại thấp (Ví dụ 8-bit) thì chắc chắn là Bot.
    Object.defineProperty(screen, 'colorDepth', {{ get: () => fp.color_depth }});
    
    // Hardware info (Preserve original pass-through CPU/RAM/Touch)
    
    // Override WebGL comment
    /*const getParameterProxy = new Proxy(WebGLRenderingContext.prototype.getParameter, {{
        apply: function(target, thisArg, args) {{
            if (args[0] === 37445) return fp.webgl_vendor;
            if (args[0] === 37446) return fp.webgl_renderer;
            return Reflect.apply(target, thisArg, args);
        }}
    }});
    WebGLRenderingContext.prototype.getParameter = getParameterProxy;

    if (typeof WebGL2RenderingContext !== 'undefined') {{
        const gp2 = new Proxy(WebGL2RenderingContext.prototype.getParameter, {{
            apply: function(target, thisArg, args) {{
                if (args[0] === 37445) return fp.webgl_vendor;
                if (args[0] === 37446) return fp.webgl_renderer;
                return Reflect.apply(target, thisArg, args);
            }}
        }});
        WebGL2RenderingContext.prototype.getParameter = gp2;
    }}
    */

    // Override doNotTrack
    Object.defineProperty(navigator, 'doNotTrack', {{ get: () => fp.do_not_track }});
}})();
"""
