## Context

`_wait_for_login_or_verify()` 仅把 `/platform` 视为登录成功。实际运行中发现，额外验证完成后站点会跳转到根路径 `/`。

## Goals / Non-Goals

**Goals:**
- 支持 `/platform` 和 `/` 两种登录成功 URL

**Non-Goals:**
- 不改动等待逻辑
- 不新增配置

## Decisions

- 在 `path in ("/", "")` 或 `"/platform" in path` 时都认为登录成功
- 保留 `/verify` 继续等待的逻辑

## Risks / Trade-offs

- 如果站点在未登录时也显示根路径，可能误判。但 CDP 流程中此时已经过验证码和邮箱验证，误判概率低。
