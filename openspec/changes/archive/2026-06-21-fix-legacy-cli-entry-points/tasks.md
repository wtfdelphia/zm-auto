## 1. 修复根目录兼容入口参数透传

- [x] 1.1 修改 `register.py`，将命令行参数透传给 `python -m zm_auto register`
- [x] 1.2 修改 `read_user_info.py`，将命令行参数透传给 `python -m zm_auto user-info`
- [x] 1.3 修改 `check_account_status.py`，将命令行参数透传给 `python -m zm_auto account-status`
- [x] 1.4 验证 `python register.py --help` 与 `python -m zm_auto register --help` 输出一致
- [x] 1.5 验证 `python read_user_info.py --help` 与 `python -m zm_auto user-info --help` 输出一致
- [x] 1.6 验证 `python check_account_status.py --help` 与 `python -m zm_auto account-status --help` 输出一致

## 2. 修复 `account-status --cdp-url` 参数

- [x] 2.1 修改 `zm_auto/cli/account_status.py`，接收 `cdp_url` 参数并透传给服务层
- [x] 2.2 修改 `zm_auto/services/account_status.py` 的 `main()`，支持通过 `cdp_url` 参数覆盖配置默认值
- [x] 2.3 验证 `python -m zm_auto account-status --cdp-url <url>` 能将指定 CDP URL 传递到服务层

## 3. 更新文档成功指标

- [x] 3.1 更新 `docs/refactor-plan.md` 中“旧 CLI 兼容入口”相关成功指标，明确参数透传可用

## 4. 可选：回归测试

- [x] 4.1 为三个根目录兼容入口添加参数透传回归测试
- [x] 4.2 为 `account-status --cdp-url` 参数覆盖添加单元测试
