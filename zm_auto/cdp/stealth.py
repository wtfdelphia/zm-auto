"""Stealth scripts for CDP pages.

借鉴 obscura / browser-act 的反检测思路：
通过 CDP 的 `addScriptToEvaluateOnNewDocument` 在页面脚本运行前注入，
隐藏自动化特征，降低被站点反爬脚本识别的概率。
"""
from __future__ import annotations

# Minified stealth script injected before any page scripts run.
STEALTH_SCRIPT = """
(() => {
  const _defineProperty = Object.defineProperty;
  const _navigator = window.navigator;

  // Hide webdriver flag
  try {
    _defineProperty(_navigator, 'webdriver', {
      get: () => undefined,
      configurable: true,
    });
  } catch (e) {}

  // Pretend to have plugins
  try {
    if (!_navigator.plugins || _navigator.plugins.length === 0) {
      _defineProperty(_navigator, 'plugins', {
        get: () => [{
          name: 'Chrome PDF Plugin',
          filename: 'internal-pdf-viewer',
          description: 'Portable Document Format',
          version: 'undefined',
          length: 1,
          item: function(idx) { return this[idx]; },
          namedItem: function() { return null; },
        }],
        configurable: true,
      });
    }
  } catch (e) {}

  // Pretend to have languages
  try {
    _defineProperty(_navigator, 'languages', {
      get: () => ['zh-CN', 'zh', 'en'],
      configurable: true,
    });
  } catch (e) {}

  // Mock window.chrome
  try {
    if (!window.chrome || Object.keys(window.chrome).length === 0) {
      _defineProperty(window, 'chrome', {
        get: () => ({
          runtime: { OnInstalledReason: { CHROME_UPDATE: 'chrome_update' } },
          loadTimes: function() { return {}; },
        }),
        configurable: true,
      });
    }
  } catch (e) {}

  // Permissions query stub
  try {
    if (_navigator.permissions && _navigator.permissions.query) {
      const originalQuery = _navigator.permissions.query;
      _navigator.permissions.query = function(...args) {
        return Promise.resolve({ state: 'prompt', onchange: null });
      };
    }
  } catch (e) {}

  // Navigator webdriver property is also exposed on chrome automations
  try {
    if ('webdriver' in _navigator) {
      delete _navigator.webdriver;
    }
  } catch (e) {}
})();
"""
