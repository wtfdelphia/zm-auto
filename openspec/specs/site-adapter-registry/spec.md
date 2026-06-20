# site-adapter-registry Specification

## Purpose

将站点特定逻辑从 service 层抽象为可插拔的 site adapter，使 zm-auto 可以按站点扩展注册/用户信息读取流程。

## Requirements

### Requirement: 定义 BaseSiteAdapter

系统 SHALL 提供 `zm_auto.sites.BaseSiteAdapter` 抽象类，包含 `name`、`site_url` 类属性，以及站点路径抽象方法：`user_info_path()`、`api_key_list_path()`、`api_key_page_path()` 和 `register_endpoints()`。

#### Scenario: 定义 zenmux adapter

- **WHEN** 实现 `ZenmuxAdapter(BaseSiteAdapter)`
- **THEN** `name == "zenmux"`
- **AND** `site_url` 从配置读取

### Requirement: 自动发现 adapter

`zm_auto.sites` SHALL 在导入时通过 `BaseSiteAdapter.__subclasses__()` 自动构建 adapter 注册表。

#### Scenario: 获取 adapter

- **WHEN** 调用 `get_site_adapter("zenmux")`
- **THEN** 返回 `ZenmuxAdapter` 实例

### Requirement: service 层 SHALL 接入 adapter

`Registrar` 和 `UserInfoService` SHALL 通过当前配置的 `site_url` 选择对应 adapter，不直接硬编码 zenmux URL 或端点路径。

#### Scenario: registrar 使用 adapter

- **WHEN** `registrar_core.py` 构造 API_BASE
- **THEN** 调用 `get_site_adapter()` 获取 `site_url`

#### Scenario: user_info 使用 adapter

- **WHEN** `user_info/core.py` 读取 user info 或 API key 列表，或导航 API key 管理页面
- **THEN** 通过 adapter 获取对应路径

