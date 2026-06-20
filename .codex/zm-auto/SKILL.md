---
name: zm-auto
description: "全自动账号注册 + API Key 获取的 Python 工具集。用于批量注册 zenmux 风格站点账号并自动导出 API Key / sub2api 配置。"
allowed-tools: [Bash]
metadata:
  author: zm-auto
  version: "0.1.0"
  homepage: "https://github.com/delphia/zm-auto"
  runtime: "Python 3.10+, dependencies: pydantic>=2, click, curl_cffi, requests, urllib3"
---

# zm-auto

全自动账号注册 + API Key 获取的 Python 工具集。

## 主要入口

```bash
# 注册账号（默认 1 个）
python -m zm_auto register -n 1

# 读取已登录账号信息，可选导出 sub2api
python -m zm_auto user-info --export-sub2api

# 账号状态诊断
python -m zm_auto account-status

# 环境/配置/Provider/CDP 状态检查
python -m zm_auto doctor
python -m zm_auto doctor --compact
```

## 能力范围

- 使用临时邮箱 provider 接收验证码（7 种 provider，见 `zm_auto/providers/`）
- 验证码求解：2captcha / anticaptcha / Playwright 浏览器 / CDP 人工介入
- 自动创建 API Key
- 导出 sub2api 兼容配置

## 安全约束

- 不要提交 `config.json`、账号输出文件或 cookies 到版本控制。
- 2captcha/anticaptcha/API Key 创建/CDP 模式等敏感操作默认需要确认，可用 `--yes` 跳过。
- CDP 模式需要先在本地启动 Chrome：`--remote-debugging-port=9222`。

## 常用验证命令

```bash
python -m compileall zm_auto/
python -m pytest tests/ -v
ruff check zm_auto/ tests/
mypy zm_auto/
python -m zm_auto --help
```
