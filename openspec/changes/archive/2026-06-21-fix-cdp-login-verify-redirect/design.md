## Context

`CDPLoginSolver.login()` 在填写验证码后通过 `_click_button()` 尝试点击"验证"按钮，然后 `page.wait_for_url("**/platform/**", timeout=15000)` 等待跳转。

实际站点行为：填写验证码后自动触发页面跳转，可能到 `/platform` 或 `/verify?method=unknown`，不需要点击按钮。

## Goals / Non-Goals

**Goals:**
- 让 CDP 登录在填写验证码后自动跟随页面跳转
- 支持 `/verify?method=unknown` 后等待 ≥15s 再跳转 `/platform`

**Non-Goals:**
- 不改动其他验证码方案
- 不改动邮箱验证码获取逻辑
- 不新增配置项

## Decisions

1. **移除对点击验证按钮的依赖**
   - 填写验证码后，直接等待 URL 变化
   - 保留点击按钮作为可选 fallback（如果页面未自动跳转）

2. **URL 轮询策略**
   - 监听 `page.url` 变化
   - 若 URL 包含 `/platform` → 登录完成
   - 若 URL 包含 `/verify` → 继续等待，超时 60s

3. **等待时间**
   - `/verify` 后默认等待 15s，可配置为 30s 以兼容慢网络

## Risks / Trade-offs

- 等待时间变长，CDP 登录整体耗时增加
- 若站点行为变化，轮询逻辑可能需要调整
