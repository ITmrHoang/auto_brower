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
STEALTH_SCRIPTS.append("""
// WebGL fingerprint spoofing
const getParameterProxy = new Proxy(WebGLRenderingContext.prototype.getParameter, {
    apply: function(target, thisArg, argumentsList) {
        const param = argumentsList[0];
        // UNMASKED_VENDOR_WEBGL
        if (param === 37445) {
            return 'Google Inc. (NVIDIA)';
        }
        // UNMASKED_RENDERER_WEBGL
        if (param === 37446) {
            return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)';
        }
        return Reflect.apply(target, thisArg, argumentsList);
    }
});
WebGLRenderingContext.prototype.getParameter = getParameterProxy;

// Also patch WebGL2
if (typeof WebGL2RenderingContext !== 'undefined') {
    const getParameterProxy2 = new Proxy(WebGL2RenderingContext.prototype.getParameter, {
        apply: function(target, thisArg, argumentsList) {
            const param = argumentsList[0];
            if (param === 37445) return 'Google Inc. (NVIDIA)';
            if (param === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)';
            return Reflect.apply(target, thisArg, argumentsList);
        }
    });
    WebGL2RenderingContext.prototype.getParameter = getParameterProxy2;
}
""")

# 8. Prevent WebRTC IP leak
STEALTH_SCRIPTS.append("""
// Block WebRTC IP leak
if (typeof RTCPeerConnection !== 'undefined') {
    const origRTC = RTCPeerConnection;
    window.RTCPeerConnection = function(...args) {
        const config = args[0] || {};
        // Force relay-only ICE candidates to prevent IP leak
        config.iceTransportPolicy = 'relay';
        return new origRTC(config);
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
