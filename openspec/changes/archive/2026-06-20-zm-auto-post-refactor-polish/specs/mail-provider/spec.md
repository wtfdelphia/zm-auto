# Mail Provider

## ADDED Requirements

### Requirement: Provider 配置校验钩子

`BaseMailProvider` SHALL 提供 `validate_config` 类方法。

#### Scenario: 子类可覆盖校验

- 子类可覆盖 `validate_config` 实现自定义校验。

### Requirement: 必填字段校验

默认实现 SHALL 校验 `required_fields` 中的字段在 config 字典中存在且非空。

#### Scenario: 缺失必填字段报错

- `BaseMailProvider` 子类设置 `required_fields = ["api_key"]` 后，`validate_config({})` 抛出 `ValueError`。
- `validate_config({"api_key": "x"})` 通过。

### Requirement: 工厂函数调用校验

`create_mailbox` SHALL 在实例化前调用校验，缺失时 SHALL 抛出异常。

#### Scenario: 校验失败阻止实例化

- 工厂函数在 `provider_class.validate_config(entry)` 失败时抛出异常，不再继续实例化。
