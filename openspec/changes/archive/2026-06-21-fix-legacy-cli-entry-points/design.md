## Context

重构为 `zm_auto` 包后，根目录的 `register.py`、`read_user_info.py`、`check_account_status.py` 被改为只调用 `from zm_auto.cli.xxx import main; main()`，未透传命令行参数。这导致旧入口名存实亡。与此同时，`account-status` 子命令虽然暴露了 `--cdp-url` 参数，但服务层并不接受该参数。

## Goals / Non-Goals

**Goals：**
- 修复三个根目录脚本的命令行参数透传，使 `python register.py -n 5` 等价于 `python -m zm_auto register -n 5`。
- 修复 `account-status --cdp-url` 参数，使其真正覆盖默认 CDP URL。
- 保持统一入口 `python -m zm_auto ...` 行为不变。

**Non-Goals：**
- 新增 CLI 子命令或参数。
- 修改注册、验证码、邮箱 provider 等业务逻辑。
- 移除旧的根目录脚本。

## Decisions

### 决策 1：脚本直接调用 `zm_auto.cli.cli(["<subcommand>", *sys.argv[1:]])`

**理由：**
- 改动最小，每个脚本只需 4 行代码。
- `click.Group` 支持通过 `args` 参数传入命令，能正确解析子命令、选项和 `--help`。
- 脚本保留原文件名，外部调用方无感知。

**备选方案：**
- 在 `zm_auto.cli` 中新增 `run_subcommand(name, args)` 辅助函数以复用异常处理。但当前 `main()` 的异常处理只是简单打印，直接调用 `cli()` 的默认行为已足够，故不引入额外抽象。

### 决策 2：`account-status --cdp-url` 从 CLI 透传到服务层

**理由：**
- 服务层 `main()` 当前无参数，只能从配置读取 CDP URL。
- 通过参数传递后，`python check_account_status.py --cdp-url http://host:9222` 才能生效。
- 保持向后兼容：默认参数为空字符串，空字符串时仍使用配置默认值。

## Risks / Trade-offs

- **[Risk] `sys.argv[0]` 在帮助文本中显示为脚本名** → 这是预期行为，`Usage: register.py [OPTIONS]` 反而对旧入口用户更自然。
- **[Risk] 直接调用 `cli()` 绕过 `main()` 的 `ZMError` 处理** → `ZMError` 目前仅在 package 内部使用，旧入口透传路径上不会触发；即便触发，`click` 默认也会打印异常。风险可接受。

## Migration Plan

- 无需数据迁移。
- 变更后，README/AGENTS 中“兼容入口”示例继续生效。
- 若用户已习惯 `python -m zm_auto ...`，行为不变。

## Open Questions

- 是否需要为三个兼容入口添加回归测试？建议添加，但属于可选。
