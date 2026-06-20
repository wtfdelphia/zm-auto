# obstacle-course Specification

## Purpose

建立基于离线 fixtures 的回归套件，在不受真实站点可用性影响的情况下，验证注册/CDP 主路径的行为稳定性。

## ADDED Requirements

### Requirement: 提供本地 fixtures 服务器

`tests/obstacle_course/conftest.py` SHALL 提供一个 fixture，在随机端口启动本地 HTTP 服务器，模拟注册流程中的关键端点（发送验证码、验证验证码、创建 API Key）。

#### Scenario: 启动本地服务

- **WHEN** fixture 启动
- **THEN** 服务监听随机端口
- **AND** 测试结束后自动关闭

### Requirement: 验证注册主路径

`tests/obstacle_course/test_register_flow.py` SHALL 使用本地 fixtures 完成一次注册流程，不依赖真实站点。

#### Scenario: 邮箱验证码注册

- **GIVEN** 本地服务模拟验证码发送与校验
- **WHEN** 调用注册相关端点
- **THEN** 返回注册成功

### Requirement: 验证 CDP 相关路径可达

`tests/obstacle_course/test_cdp_flow.py` SHALL 使用本地页面或 mock page 验证 CDP 相关调用不报错。

#### Scenario: fixtures 服务响应 user info

- **WHEN** 访问 `/api/user/info`
- **THEN** 返回合法 JSON
- **AND** 包含邮箱字段
