# cdp-stealth Specification

## Purpose

在通过 CDP 控制的 Playwright page 上注入反检测脚本，降低自动化操作被站点反爬脚本识别的概率。

## ADDED Requirements

### Requirement: CDPSession 支持注入 stealth 脚本

`CDPSession` SHALL 提供 `add_stealth_scripts(page)` 方法，通过 `Page.addScriptToEvaluateOnNewDocument` 注入反检测脚本。

#### Scenario: stealth 脚本注入成功

- **WHEN** 调用 `add_stealth_scripts(page)`
- **THEN** page 执行后 `navigator.webdriver` 为 `undefined`
- **AND** `window.chrome` 存在且不为空对象

### Requirement: stealth 脚本覆盖常见检测点

注入脚本 SHALL 覆盖 `navigator.webdriver`、`plugins`、`languages`、`window.chrome`、`navigator.permissions` 中的至少五项。

#### Scenario: 检测点被隐藏或伪装

- **WHEN** 页面加载后执行 JS
- **THEN** `navigator.webdriver === undefined`
- **AND** `navigator.plugins.length > 0`
- **AND** `navigator.languages` 为非空数组
- **AND** `window.chrome.runtime` 存在
- **AND** `navigator.permissions.query` 可用

### Requirement: stealth 注入幂等

对同一 page 重复调用 `add_stealth_scripts()` SHALL 不会导致脚本重复生效或报错。

#### Scenario: 重复注入

- **WHEN** 对同一 page 调用两次 `add_stealth_scripts(page)`
- **THEN** 第二次调用不抛出异常
- **AND** 页面检测点结果与第一次一致
