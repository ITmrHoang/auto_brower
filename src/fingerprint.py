"""
Fingerprint Generator for Auto-Browser.
Generates random but consistent browser fingerprints per profile.
"""

import random
import hashlib
import json
import requests
from typing import Optional


# Common screen resolutions
SCREEN_RESOLUTIONS = [
    (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
    (1280, 720), (1600, 900), (2560, 1440), (1280, 800),
    (1024, 768), (1680, 1050),
]

# Common timezones
TIMEZONES = [
    "America/New_York", "America/Chicago", "America/Denver",
    "America/Los_Angeles", "Europe/London", "Europe/Paris",
    "Europe/Berlin", "Asia/Tokyo", "Asia/Shanghai",
    "Australia/Sydney", "Asia/Ho_Chi_Minh",
]

# Common platforms
PLATFORMS = ["Win32", "Win64", "MacIntel", "Linux x86_64"]

# Common WebGL renderers (Mở rộng để đa dạng hóa)
WEBGL_RENDERERS = [
    # NVIDIA GeForce Series
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 3GB Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1070 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Laptop GPU Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    
    # AMD Radeon Series
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 570 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 6600 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 7900 XTX Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Ryzen 5 5600G with Radeon Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    
    # Intel Graphics
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) HD Graphics 520 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    
    # Apple M-Series (macOS specific renderers)
    ("Apple", "Apple M1"),
    ("Apple", "Apple M1 Pro"),
    ("Apple", "Apple M1 Max"),
    ("Apple", "Apple M2"),
    ("Apple", "Apple M2 Pro"),
    ("Apple", "Apple M3"),
]

# Common user agents (Mở rộng cho nhiều loại trình duyệt phổ biến)
USER_AGENTS = [
    # Windows Chrome (115 - 124)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    
    # Windows Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",

    # macOS Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; ARM Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
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


def generate_fingerprint(seed: Optional[str] = None, proxy: Optional[str] = None) -> dict:
    """
    Generate a random but deterministic fingerprint.
    If seed is provided, the same seed always produces the same fingerprint.
    If proxy is provided, it tries to detect correct timezone and language from that IP.
    """
    if seed:
        rng = random.Random(hashlib.md5(seed.encode()).hexdigest())
    else:
        rng = random.Random()

    screen = rng.choice(SCREEN_RESOLUTIONS)
    webgl = rng.choice(WEBGL_RENDERERS)
    
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

    fingerprint = {
        "screen_width": screen[0],
        "screen_height": screen[1],
        "color_depth": rng.choice([24, 32]),
        "timezone": timezone,
        "platform": rng.choice(PLATFORMS),
        "user_agent": rng.choice(USER_AGENTS),
        "languages": languages,
        "webgl_vendor": webgl[0],
        "webgl_renderer": webgl[1],
        "hardware_concurrency": rng.choice([4, 6, 8, 12, 16]),
        "device_memory": rng.choice([4, 8, 16]),
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

    // Override screen
    Object.defineProperty(screen, 'width', {{ get: () => fp.screen_width }});
    Object.defineProperty(screen, 'height', {{ get: () => fp.screen_height }});
    Object.defineProperty(screen, 'availWidth', {{ get: () => fp.screen_width }});
    Object.defineProperty(screen, 'availHeight', {{ get: () => fp.screen_height - 40 }});
    Object.defineProperty(screen, 'colorDepth', {{ get: () => fp.color_depth }});

    // Override hardware info
    Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => fp.hardware_concurrency }});
    Object.defineProperty(navigator, 'deviceMemory', {{ get: () => fp.device_memory }});
    Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => fp.max_touch_points }});

    // Override WebGL
    const getParameterProxy = new Proxy(WebGLRenderingContext.prototype.getParameter, {{
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

    // Override doNotTrack
    Object.defineProperty(navigator, 'doNotTrack', {{ get: () => fp.do_not_track }});
}})();
"""
