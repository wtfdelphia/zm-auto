## Context

`CDPLoginSolver.logout()` 当前通过 `page.goto("{site_url}/logout")` 导航到退出页面，但目标站点的实际退出接口是 `POST /api/user/logout?ctoken=<ctoken>`。

## Goals / Non-Goals

**Goals:**
- 调用正确的服务端退出接口
- 使用浏览器 cookies 中的 `ctoken`

**Non-Goals:**
- 不改动登录流程
- 不新增配置项

## Decisions

1. 从 `page.context.cookies()` 中提取 `ctoken`
2. 使用 `requests` 或 `curl_cffi` 发送 POST 请求
3. 保留页面导航作为 fallback

## Risks / Trade-offs

- 若浏览器 cookies 中无 `ctoken`，退出会失败，但不会影响注册结果
