"""
Fingerprint Generator for Auto-Browser.
Generates random but consistent browser fingerprints per profile.
"""

import random
import hashlib
import json
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

# Common WebGL renderers
WEBGL_RENDERERS = [
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
]

# Common user agents (Chrome on Windows)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# Languages
LANGUAGE_SETS = [
    ["en-US", "en"],
    ["en-GB", "en"],
    ["vi-VN", "vi", "en-US", "en"],
    ["fr-FR", "fr", "en"],
    ["de-DE", "de", "en"],
    ["ja-JP", "ja", "en"],
]


def generate_fingerprint(seed: Optional[str] = None) -> dict:
    """
    Generate a random but deterministic fingerprint.
    If seed is provided, the same seed always produces the same fingerprint.
    """
    if seed:
        rng = random.Random(hashlib.md5(seed.encode()).hexdigest())
    else:
        rng = random.Random()

    screen = rng.choice(SCREEN_RESOLUTIONS)
    webgl = rng.choice(WEBGL_RENDERERS)

    fingerprint = {
        "screen_width": screen[0],
        "screen_height": screen[1],
        "color_depth": rng.choice([24, 32]),
        "timezone": rng.choice(TIMEZONES),
        "platform": rng.choice(PLATFORMS),
        "user_agent": rng.choice(USER_AGENTS),
        "languages": rng.choice(LANGUAGE_SETS),
        "webgl_vendor": webgl[0],
        "webgl_renderer": webgl[1],
        "hardware_concurrency": rng.choice([4, 6, 8, 12, 16]),
        "device_memory": rng.choice([4, 8, 16]),
        "do_not_track": rng.choice([None, "1"]),
        "max_touch_points": 0,
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
