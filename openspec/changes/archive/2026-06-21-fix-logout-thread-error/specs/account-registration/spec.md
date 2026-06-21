## MODIFIED Requirements

### Requirement: CDP 方案注册完成后退出登录

系统 SHALL 在注册流程的所有输出文件写入完成后，再调用服务端退出登录接口。系统 SHALL 使用 HTTP POST 调用 `https://zenmux.ai/api/user/logout?ctoken=<ctoken>`，而不是通过 CDP 浏览器 evaluate 调用，以避免跨线程访问 Playwright page 对象。

#### Scenario: CDP 注册成功后不触发线程错误

- **WHEN** 用户执行 `python -m zm_auto register -n 1 --export-sub2api` 且使用 CDP provider
- **AND** 注册成功，文件写入完成
- **THEN** 系统在主线程发起 HTTP POST 到 `/api/user/logout?ctoken=<ctoken>`
- **AND** 不访问 worker 线程创建的 Playwright page 对象
- **AND** 不抛出 `cannot switch to a different thread` 异常

#### Scenario: CDP 浏览器 session 在 worker 线程关闭

- **WHEN** CDP 注册流程结束（成功或失败）
- **THEN** `Registrar.close()` 在 worker 线程内关闭 Playwright 浏览器 session
- **AND** 不产生跨线程访问错误
