"""
Stealth module for Auto-Browser.
Injects JavaScript to bypass bot detection mechanisms.
"""

# JavaScript snippets to inject into every page to evade bot detection

STEALTH_SCRIPTS = []

# 1. Remove navigator.webdriver flag
STEALTH_SCRIPTS.append("""
// Remove webdriver flag
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});
""")

# 2. Override navigator.plugins to look like a real browser
STEALTH_SCRIPTS.append("""
// Fake plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
        ];
        plugins.length = 3;
        return plugins;
    },
});
""")

# 3. Override navigator.languages
STEALTH_SCRIPTS.append("""
// Override languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
});
""")

# 4. Fix Chrome runtime (make it look like a real Chrome)
STEALTH_SCRIPTS.append("""
// Add chrome runtime
if (!window.chrome) {
    window.chrome = {};
}
if (!window.chrome.runtime) {
    window.chrome.runtime = {
        connect: function() {},
        sendMessage: function() {},
        onMessage: { addListener: function() {} },
    };
}
""")

# 5. Override permissions API
STEALTH_SCRIPTS.append("""
// Override permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => {
    if (parameters.name === 'notifications') {
        return Promise.resolve({ state: Notification.permission });
    }
    return originalQuery(parameters);
};
""")

# 6. Canvas fingerprint protection (add subtle noise)
STEALTH_SCRIPTS.append("""
// Canvas fingerprint noise
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(type) {
    if (type === 'image/png' || type === undefined) {
        const context = this.getContext('2d');
        if (context) {
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                // Add subtle noise to RGB channels
                imageData.data[i] = imageData.data[i] ^ (Math.random() > 0.5 ? 1 : 0);
                imageData.data[i+1] = imageData.data[i+1] ^ (Math.random() > 0.5 ? 1 : 0);
                imageData.data[i+2] = imageData.data[i+2] ^ (Math.random() > 0.5 ? 1 : 0);
            }
            context.putImageData(imageData, 0, 0);
        }
    }
    return originalToDataURL.apply(this, arguments);
};
""")

# 7. WebGL vendor/renderer spoofing
# STEALTH_SCRIPTS.append("""
# // WebGL fingerprint spoofing
# const getParameterProxy = new Proxy(WebGLRenderingContext.prototype.getParameter, {
#     apply: function(target, thisArg, argumentsList) {
#         const param = argumentsList[0];
#         // UNMASKED_VENDOR_WEBGL
#         if (param === 37445) {
#             return 'Google Inc. (NVIDIA)';
#         }
#         // UNMASKED_RENDERER_WEBGL
#         if (param === 37446) {
#             return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)';
#         }
#         return Reflect.apply(target, thisArg, argumentsList);
#     }
# });
# WebGLRenderingContext.prototype.getParameter = getParameterProxy;

# // Also patch WebGL2
# if (typeof WebGL2RenderingContext !== 'undefined') {
#     const getParameterProxy2 = new Proxy(WebGL2RenderingContext.prototype.getParameter, {
#         apply: function(target, thisArg, argumentsList) {
#             const param = argumentsList[0];
#             if (param === 37445) return 'Google Inc. (NVIDIA)';
#             if (param === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)';
#             return Reflect.apply(target, thisArg, argumentsList);
#         }
#     });
#     WebGL2RenderingContext.prototype.getParameter = getParameterProxy2;
# }
# """)
# 7. WebGL vendor/renderer spoofing (Bỏ qua - Đã được chuyển giao cho fingerprint.py đồng bộ)
# Việc ghi đè WebGL sẽ được thực hiện tại `fingerprint_to_stealth_script` bằng dữ liệu GPU random theo từng profile.

# 8. WebRTC Public IP Spoofing (Or Relay-Only Fallback)
STEALTH_SCRIPTS.append("""
// WebRTC Spoofing
if (typeof RTCPeerConnection !== 'undefined') {
    const origRTC = RTCPeerConnection;
    window.RTCPeerConnection = function(...args) {
        const config = args[0] || {};
        const publicIp = (typeof fp !== 'undefined' && fp.public_ip) ? fp.public_ip : null;
        
        // Chặn rò rỉ nếu không có Public IP (An toàn dự phòng)
        if (!publicIp) {
            config.iceTransportPolicy = 'relay';
        }
        
        const pc = new origRTC(config);
        
        if (publicIp) {
            // Đè cơ chế Event Listener để Fake IP của icecandidate
            const origAddEventListener = pc.addEventListener;
            pc.addEventListener = function(type, listener, options) {
                if (type === 'icecandidate') {
                    const fakeListener = function(event) {
                        if (event.candidate && event.candidate.candidate) {
                            event.candidate.candidate = event.candidate.candidate.replace(
                                /([0-9]{1,3}(\\.[0-9]{1,3}){3}|[a-f0-9]{1,4}(:[a-f0-9]{1,4}){7})/, 
                                publicIp
                            );
                        }
                        return listener.call(this, event);
                    };
                    return origAddEventListener.call(this, type, fakeListener, options);
                }
                return origAddEventListener.call(this, type, listener, options);
            };
            
            // Xử lý nốt thuộc tính gán trực tiếp pc.onicecandidate
            Object.defineProperty(pc, 'onicecandidate', {
                set(listener) {
                    this._onicecandidate = listener;
                    origAddEventListener.call(this, 'icecandidate', (event) => {
                        if (this._onicecandidate) {
                            if (event.candidate && event.candidate.candidate) {
                                let cStr = event.candidate.candidate;
                                cStr = cStr.replace(/([0-9]{1,3}(\\.[0-9]{1,3}){3}|[a-f0-9]{1,4}(:[a-f0-9]{1,4}){7})/, publicIp);
                                Object.defineProperty(event.candidate, 'candidate', {get: () => cStr});
                                Object.defineProperty(event.candidate, 'address', {get: () => publicIp});
                            }
                            this._onicecandidate(event);
                        }
                    });
                },
                get() { return this._onicecandidate; }
            });
        }
        return pc;
    };
    window.RTCPeerConnection.prototype = origRTC.prototype;
}
""")

# 9. Mock navigator.hardwareConcurrency and deviceMemory
STEALTH_SCRIPTS.append("""
// Mock hardware info
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
""")

# 10. Fix iframe contentWindow check
STEALTH_SCRIPTS.append("""
// Prevent iframe detection
try {
    const elementDescriptor = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
    if (elementDescriptor) {
        Object.defineProperty(HTMLDivElement.prototype, 'offsetHeight', {
            ...elementDescriptor,
        });
    }
} catch(e) {}
""")

# 11. AudioContext Fingerprint Spoofing (Thêm nhiễu sóng âm thanh)
STEALTH_SCRIPTS.append("""
// AudioContext spoofing
const originalGetChannelData = AudioBuffer.prototype.getChannelData;
AudioBuffer.prototype.getChannelData = function(channel) {
    const results = originalGetChannelData.apply(this, arguments);
    for (let i = 0; i < results.length; i += 100) {
        results[i] = results[i] + (Math.random() * 0.0000001); // Thêm nhiễu siêu vi không nghe được
    }
    return results;
};
""")

# 12. DOMRect / ClientRects Fingerprint Spoofing (Làm mờ kích thước phần tử HTML)
# STEALTH_SCRIPTS.append("""
# // DOMRect spoofing
# const originalGetBoundingClientRect = Element.prototype.getBoundingClientRect;
# Element.prototype.getBoundingClientRect = function() {
#     const rect = originalGetBoundingClientRect.apply(this, arguments);
#     const noise = () => Math.random() * 0.00001;
#     return {
#         x: rect.x + noise(),
#         y: rect.y + noise(),
#         width: rect.width + noise(),
#         height: rect.height + noise(),
#         top: rect.top + noise(),
#         right: rect.right + noise(),
#         bottom: rect.bottom + noise(),
#         left: rect.left + noise(),
#         toJSON: rect.toJSON
#     };
# };
# """)

# 13. Battery API Spoofing (Thuật toán Pin thật: Có sạc, có tụt, có sạc đầy 100%)
STEALTH_SCRIPTS.append("""
// Battery spoofing
if (navigator.getBattery) {
    let fakeBattery = {};
    const isFull = Math.random() < 0.25; // 25% cơ hội máy tính cắm sạc đầy 100%
    
    if (isFull) {
        fakeBattery = {
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity,
            level: 1.0,
            onchargingchange: null,
            onchargingtimechange: null,
            ondischargingtimechange: null,
            onlevelchange: null
        };
    } else {
        const isCharging = Math.random() < 0.3; // 30% cơ hội đang cắm sạc nhưng chưa đầy
        let currentLevel = 0.3 + (Math.random() * 0.65); // Mức pin random 30% - 95%
        
        fakeBattery = {
            charging: isCharging,
            chargingTime: isCharging ? Math.floor(Math.random() * 5000) : Infinity,
            dischargingTime: isCharging ? Infinity : Math.floor(Math.random() * 15000),
            level: currentLevel,
            onchargingchange: null,
            onchargingtimechange: null,
            ondischargingtimechange: null,
            onlevelchange: null
        };
        
        // Mô phỏng tụt/tăng pin rùa bò mỗi 2 phút (chống check tĩnh)
        setInterval(() => {
            if (fakeBattery.charging && fakeBattery.level < 1.0) {
                fakeBattery.level = Math.min(1.0, fakeBattery.level + 0.01);
            } else if (!fakeBattery.charging && fakeBattery.level > 0.05) {
                fakeBattery.level = Math.max(0.01, fakeBattery.level - 0.01);
            }
        }, 120000); 
    }
    navigator.getBattery = () => Promise.resolve(fakeBattery);
}
""")


# 14. Canvas Fingerprint Spoofing (Cấy độ nhiễu màu sắc Cố định theo Seed)
STEALTH_SCRIPTS.append("""
// Canvas spoofing
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

const shift = {
    r: (typeof fp !== 'undefined' && fp.canvas_noise) ? fp.canvas_noise.r : 1,
    g: (typeof fp !== 'undefined' && fp.canvas_noise) ? fp.canvas_noise.g : 1,
    b: (typeof fp !== 'undefined' && fp.canvas_noise) ? fp.canvas_noise.b : 1
};

HTMLCanvasElement.prototype.toDataURL = function(...args) {
    const context = this.getContext('2d');
    if (context) {
        const width = this.width;
        const height = this.height;
        if (width > 0 && height > 0) {
            const imageData = context.getImageData(0, 0, width, height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] = imageData.data[i] + shift.r;
                imageData.data[i + 1] = imageData.data[i + 1] + shift.g;
                imageData.data[i + 2] = imageData.data[i + 2] + shift.b;
            }
            context.putImageData(imageData, 0, 0);
        }
    }
    return originalToDataURL.apply(this, args);
};

CanvasRenderingContext2D.prototype.getImageData = function(...args) {
    const imageData = originalGetImageData.apply(this, args);
    for (let i = 0; i < imageData.data.length; i += 4) {
        imageData.data[i] = Math.max(0, Math.min(255, imageData.data[i] + shift.r));
        imageData.data[i + 1] = Math.max(0, Math.min(255, imageData.data[i + 1] + shift.g));
        imageData.data[i + 2] = Math.max(0, Math.min(255, imageData.data[i + 2] + shift.b));
    }
    return imageData;
};
""")

# 15. Font Fingerprinting Spoofing (Cấy nhiễu sai số viền Font)
STEALTH_SCRIPTS.append("""
// Font spoofing
const origOffsetWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetWidth');
const fontNoise = (typeof fp !== 'undefined' && fp.font_noise) ? fp.font_noise : 0.05;

Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
    get() {
        const val = origOffsetWidth.get.call(this);
        // Add minimal subpixel noise to span width when bot tries to measure font sizes
        if (this.tagName === 'SPAN' && val > 0 && val < 500) {
            return val + fontNoise;
        }
        return val;
    }
});
""")

# 16. Media Devices Hashing Spoofing (Giả mạo số lượng cắm Microphone / Webcam bằng Seed)
STEALTH_SCRIPTS.append("""
// Media Devices Spoofing
if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
    const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);
    navigator.mediaDevices.enumerateDevices = async function() {
        await originalEnumerateDevices(); // Let it prompt permissions if needed
        const fakeDevices = [];
        const mediaConfigs = (typeof fp !== 'undefined' && fp.media_devices) ? fp.media_devices : {audio_in: 1, audio_out: 1, video_in: 0};
        
        // Generate pseudo-random deterministic IDs based on user agent (Seed bounds)
        const mkId = (pref, idx) => btoa((typeof fp !== 'undefined' ? fp.user_agent : pref) + idx).substring(0, 32);
        
        for (let i=0; i < mediaConfigs.audio_in; i++) {
            fakeDevices.push({ kind: 'audioinput', deviceId: mkId('ai', i), groupId: mkId('grp', i), label: 'Default Microphone ' + i });
        }
        for (let i=0; i < mediaConfigs.audio_out; i++) {
            fakeDevices.push({ kind: 'audiooutput', deviceId: mkId('ao', i), groupId: mkId('grp', i), label: 'Default Speaker ' + i });
        }
        for (let i=0; i < mediaConfigs.video_in; i++) {
            fakeDevices.push({ kind: 'videoinput', deviceId: mkId('vi', i), groupId: mkId('grp', i), label: 'FHD Webcam ' + i });
        }
        
        return fakeDevices.map(d => {
            const proto = Object.create(MediaDeviceInfo.prototype);
            return Object.assign(proto, d);
        });
    };
}
""")

def get_combined_stealth_script() -> str:
    """Get all stealth scripts combined into one."""
    return "\n".join([
        "(function() {",
        "\n".join(STEALTH_SCRIPTS),
        "})();"
    ])


def get_stealth_scripts() -> list:
    """Get individual stealth scripts."""
    return STEALTH_SCRIPTS
