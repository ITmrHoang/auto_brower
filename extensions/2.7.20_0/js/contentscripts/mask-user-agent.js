const processMaskUserAgent = function processMaskUserAgent(userAgent) {
  const regExp = /(?<=\/)[^ ]+/m;
  const appVersion = regExp.exec(userAgent)[0];

  return `(() => {
    Object.defineProperties(Navigator.prototype, {
      appVersion: {
        value: '${appVersion}',
        configurable: false,
        enumerable: true,
        writable: false
      },
      userAgent: {
        value: '${userAgent}',
        configurable: false,
        enumerable: true,
        writable: false
      }
    });
  })();`;
};

chrome.runtime.sendMessage({ request: 'MaskUserAgent' }, (response) => {
  if (!response) return;

  const script = document.createElement('script');
  script.textContent = processMaskUserAgent(response);
  document.documentElement.appendChild(script);
  script.remove();
});
