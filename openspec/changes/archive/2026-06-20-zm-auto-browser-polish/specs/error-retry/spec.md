# error-retry Specification

## Purpose

统一 zm-auto 内部错误表示与重试策略，减少 provider/CDP 调用中因临时网络波动或页面未就绪导致的偶发失败。

## ADDED Requirements

### Requirement: 定义统一错误基类

系统 SHALL 提供 `zm_auto.errors.ZmAutoError` 作为所有业务错误的基类，包含 `message` 和可选 `hint` 字段。

#### Scenario: 创建错误

- **WHEN** 抛出 `ZmAutoError("network timeout", hint="check proxy")`
- **THEN** `str(error)` 包含 `network timeout`
- **AND** `error.hint == "check proxy"`

### Requirement: 支持可重试错误标记

系统 SHALL 提供 `RetryableError`  mixin/基类，被标记的错误 SHALL 可被 `with_retry` 自动重试。

#### Scenario: 标记错误可重试

- **WHEN** 自定义异常继承 `RetryableError`
- **THEN** `with_retry` 在捕获该异常时执行重试

### Requirement: 提供统一重试辅助函数

系统 SHALL 提供 `with_retry(func, policy=None)`，支持按次数、指数退避、可重试异常类型进行调用。

#### Scenario: 成功无需重试

- **WHEN** 传入的函数第一次调用即成功
- **THEN** `with_retry` 直接返回结果，不等待

#### Scenario: 临时失败重试后成功

- **WHEN** 函数前两次抛出 `RetryableError`，第三次成功
- **THEN** `with_retry` 返回第三次结果
- **AND** 总调用次数为 3

#### Scenario: 超过最大重试次数失败

- **WHEN** 函数始终抛出 `RetryableError`
- **THEN** `with_retry` 在最后一次失败后抛出 `RetryExhaustedError`

### Requirement: 默认重试策略可配置

`RetryPolicy` SHALL 允许设置最大重试次数、初始延迟、最大延迟、退避倍数、可重试异常类型。

#### Scenario: 自定义退避

- **WHEN** 设置 `backoff=1.0, max_delay=5.0`
- **THEN** 重试间隔不超过 5 秒，且第一次失败后立即重试（间隔 0）
