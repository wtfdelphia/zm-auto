## Why

重构为 `zm_auto` 包后，README 与 AGENTS.md 仍声明根目录脚本 `register.py`、`read_user_info.py`、`check_account_status.py` 为“兼容入口”。但当前这三个脚本仅直接调用 `main()`，不接收任何命令行参数，导致 `python register.py -n 5` 被忽略、`--help` 无法显示。这与文档描述不符，也给依赖旧命令的外部脚本带来困扰。

本次变更在不改变统一入口 `python -m zm_auto ...` 的前提下，修复薄兼容入口，使其真正可用。

## What Changes

- 修复 `register.py`、`read_user_info.py`、`check_account_status.py`，将 `sys.argv` 透传给 `python -m zm_auto` 的对应子命令。
- 修复 `account-status` 子命令的 `--cdp-url` 参数：CLI handler 将 `cdp_url` 传给服务层，服务层 `main()` 支持通过参数覆盖默认 CDP URL。
- 更新 `docs/refactor-plan.md` 成功指标，明确旧入口“透传参数可用”。
- （可选）补充三个薄兼容入口的回归测试。

## Capabilities

### New Capabilities

- 无

### Modified Capabilities

- `account-registration`：文档中关于“根目录保留 `register.py` 薄兼容入口”的条款，从“保留入口”细化为“入口必须透传 CLI 参数”。

## Impact

- 仅影响根目录三个兼容脚本和 `zm_auto/cli/account_status.py` / `zm_auto/services/account_status.py`。
- 不改动注册流程、验证码、邮箱 provider、CDP 核心逻辑等业务代码。
- 不引入新依赖。
