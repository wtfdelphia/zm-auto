## MODIFIED Requirements

### Requirement: CDP 方案注册完成后退出登录

系统 SHALL 在注册流程的所有输出文件（`accounts.json`、`sub2api_export.json`）写入完成后，再调用 CDP 浏览器退出登录接口。

#### Scenario: 成功注册后按正确时序退出

- **WHEN** 用户执行 `python -m zm_auto register -n 1 --export-sub2api` 且使用 CDP provider
- **THEN** 系统完成注册后先将结果写入 `accounts.json`
- **AND** 系统完成 `--export-sub2api` 导出后写入 `sub2api_export.json`
- **AND** 最后调用 `https://zenmux.ai/api/user/logout?ctoken=<ctoken>` 退出浏览器 session
- **AND** 退出登录前文件已持久化

#### Scenario: 注册失败后仍按正确时序退出

- **WHEN** CDP 登录阶段失败
- **THEN** 系统仍将部分邮箱信息写入 `accounts.json`
- **AND** 文件写入完成后调用服务端退出接口
- **AND** 不会提前登出导致结果丢失
