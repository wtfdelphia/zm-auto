## ADDED Requirements

### Requirement: Pydantic 配置模型

系统 SHALL 使用 Pydantic v2 BaseModel 定义配置 Schema，替代分散的 dict 取值。

#### Scenario: Config 模型定义完整

- **WHEN** 检查 `zm_auto/config.py` 中的 Config 类
- **THEN** 包含 `mail`、`proxy`、`total`、`threads`、`captcha`、`api_key_name`、`site_url`、`invite_code`、`logout_after`、`on_waitlist`、`waitlist_logout`、`sub2api`、`auto_create_api_key` 字段
- **AND** 所有字段有类型注解和默认值

#### Scenario: Mail config 支持 discriminated union

- **WHEN** 加载包含 `mail.providers[].type` 为 `"cloudflare_temp_email"` 的配置
- **THEN** 对应的 provider 配置被解析为 `CloudflareProviderConfig` 实例
- **AND** 包含 `api_base`、`admin_password`、`domain` 等字段

#### Scenario: Captcha config 扁平结构

- **WHEN** 加载包含 `captcha.provider` 为 `"2captcha"` 的配置
- **THEN** `config.captcha.api_key` 返回配置的 API Key 字符串
- **AND** 不需要 `config.captcha.2captcha.api_key` 嵌套访问

#### Scenario: Captcha provider 支持所有验证码方案

- **WHEN** 检查 `CaptchaConfig.provider` 字段的类型
- **THEN** 接受 `"2captcha"`、`"anticaptcha"`、`"browser"`、`"cdp"` 四个值
- **AND** 非法值在加载时抛出 ValidationError

### Requirement: 配置加载兼容

系统 SHALL 从 `config.json` 加载配置，不存在时使用默认值，多余字段不报错。

#### Scenario: 无 config.json 时使用默认值

- **WHEN** `config.json` 不存在
- **THEN** 返回完整的默认 Config 对象
- **AND** 所有字段为默认值

#### Scenario: 部分字段覆盖

- **WHEN** `config.json` 仅包含 `{"proxy": "http://127.0.0.1:7890"}`
- **THEN** 返回的 Config 对象中 `proxy` 为 `"http://127.0.0.1:7890"`
- **AND** 其余字段均为默认值

#### Scenario: 多余字段不报错

- **WHEN** `config.json` 包含 Schema 中未定义的字段（如 `_comment`）
- **THEN** 配置加载成功，不抛出 ValidationError

### Requirement: config.example.json 一致性

`config.example.json` 的字段结构 SHALL 与 DEFAULT_CONFIG 保持一致。

#### Scenario: 字段结构一致

- **WHEN** 比对 `config.example.json` 与 `DEFAULT_CONFIG` 的顶层字段
- **THEN** 两者包含相同的字段名
- **AND** 不包含 `headless`（顶层）和 `_comment_captcha` 字段
- **AND** 包含 `captcha.browser.user_data_dir`、`sub2api.export`、`auto_create_api_key` 字段

#### Scenario: 默认值一致

- **THEN** `wait_interval` 统一为 `2`
- **AND** `site_url` 统一为 `"https://example.com"`
- **AND** `sub2api.upstream_base_url` 统一为空字符串 `""`
- **AND** 所有共享字段的默认值相同
