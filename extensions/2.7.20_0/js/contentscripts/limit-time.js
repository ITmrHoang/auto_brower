const ZINDEX = 2147483647;

const DEFAULT_IFRAME_STYLES = {
  position: 'fixed',
  inset: 0,
  zIndex: ZINDEX,
  maxWidth: '100%',
  maxHeight: '100%',
  height: '100%',
  width: '100%',
  overflow: 'hidden',
  backgroundColor: 'transparent',
  visibility: 'visible',
  display: 'block',
  colorScheme: 'none',
  border: 'none',
  pointerEvents: 'none',
};

const DEFAULT_SHADE_STYLES = {
  position: 'fixed',
  inset: 'auto 0 0 auto',
  zIndex: ZINDEX - 1,
  height: '112px',
  width: '228px',
};

const IFRAME_ID = '_veepn_iframe__base';
const IFRAME_SHADE_ID = '_veepn_iframe__shade';
const IFRAME_URL = `${chrome.runtime.getURL('')}popup/index.html`;

const getInjectableParent = function getInjectableParent() {
  return document && document.body;
};

const createIframeWidget = function createIframeWidget() {
  const parent = getInjectableParent();
  const oldFrame = document.getElementById(IFRAME_ID);

  if (!parent || oldFrame) return;

  // add iframe
  const frame = document.createElement('iframe');

  frame.src = IFRAME_URL;
  frame.id = IFRAME_ID;

  Object.assign(frame.style, DEFAULT_IFRAME_STYLES);

  parent.appendChild(frame);

  // add shade div
  const shade = document.createElement('div');

  shade.id = IFRAME_SHADE_ID;

  shade.onmouseenter = () => {
    frame.style.pointerEvents = 'all';
  };

  Object.assign(shade.style, DEFAULT_SHADE_STYLES);

  parent.appendChild(shade);
};

const removeIframeWidget = function removeIframeWidget() {
  const frame = document.getElementById(IFRAME_ID);

  if (frame) {
    frame.remove();
  }

  const div = document.getElementById(IFRAME_SHADE_ID);

  if (div) {
    div.remove();
  }
};

const handleExtensionEvents = function handleExtensionEvents(req) {
  if (req.msg === 'lt-proxy-connected') {
    const isExclude = req.exclude.some((item) =>
      window.location.host.includes(item),
    );

    if (!isExclude) {
      createIframeWidget();
    }
  } else if (req.msg === 'lt-proxy-disconnected') {
    removeIframeWidget();
  }

  // sendResponse(null);
};

chrome.runtime.onMessage.addListener(handleExtensionEvents);

window.addEventListener('unload', () => {
  chrome.runtime.onMessage.removeListener(handleExtensionEvents);
});

chrome.runtime.sendMessage({ msg: 'lt-get-proxy-status' }, (res) => {
  if (!(res && res.exclude)) return;

  const isExclude = res.exclude.some((item) =>
    window.location.host.includes(item),
  );

  if (res.isConnected && !isExclude) {
    createIframeWidget();
  }
});

window.addEventListener('message', (req) => {
  const { msg, data } = req.data;

  if (msg === 'lt-iframe-resize') {
    const frame = document.getElementById(IFRAME_ID);

    if (frame) {
      Object.assign(frame.style, DEFAULT_IFRAME_STYLES, data);
    }
  }
});
