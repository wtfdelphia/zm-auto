"""Command registry for click CLI.

借鉴 bb-browser 的 `packages/shared/src/commands.ts` 设计思想：
所有子命令的元数据集中在 COMMANDS 注册表中声明，click 子命令、help 文档、
未来 AI Agent 调用 schema 都从同一个数据源生成，避免分散在多个文件。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ParamDef:
    """CLI 参数定义。"""

    name: str
    type: Literal["string", "number", "boolean"] = "string"
    default: Any = None
    help: str = ""
    is_flag: bool = False
    flag: str = ""  # noqa: A003

    @property
    def option_name(self) -> str:
        return "--" + self.name.replace("_", "-")

    def to_json_schema(self) -> dict[str, Any]:
        """生成该参数的 JSON Schema 片段，供 AI Agent / 文档使用。"""
        type_map = {
            "string": "string",
            "number": "number",
            "boolean": "boolean",
        }
        schema: dict[str, Any] = {
            "type": type_map.get(self.type, "string"),
            "description": self.help,
        }
        if self.default is not None:
            schema["default"] = self.default
        return schema


@dataclass
class CommandDef:
    """CLI 命令定义。"""

    name: str
    group: str
    description: str
    handler: str
    params: list[ParamDef] = field(default_factory=list)

    def to_json_schema(self) -> dict[str, Any]:
        """生成该命令的 JSON Schema，用于 AI Agent 调用签名。"""
        properties: dict[str, dict[str, Any]] = {}
        required: list[str] = []
        for p in self.params:
            properties[p.name] = p.to_json_schema()
            if p.default is None and not p.is_flag:
                required.append(p.name)
        schema: dict[str, Any] = {
            "type": "object",
            "description": self.description,
            "properties": properties,
        }
        if required:
            schema["required"] = required
        return schema

    def to_json_schema_str(self) -> str:
        """生成该命令的 JSON Schema 字符串。"""
        import json

        return json.dumps(self.to_json_schema(), ensure_ascii=False, indent=2)


# Single source of truth for CLI commands metadata.
COMMANDS: list[CommandDef] = [
    CommandDef(
        name="register",
        group="auth",
        description="""自动注册账号并获取 API Key。""",
        handler="zm_auto.cli.register:main",
        params=[
            ParamDef("total", "number", None, "注册数量", flag="-n"),
            ParamDef("threads", "number", None, "并发数", flag="-t"),
            ParamDef("proxy", "string", "", "代理地址"),
            ParamDef("yes", "boolean", False, "跳过敏感操作确认", is_flag=True, flag="--yes"),
        ],
    ),
    CommandDef(
        name="user-info",
        group="user",
        description="""读取已登录账号信息，支持导出 sub2api。""",
        handler="zm_auto.cli.user_info:main",
        params=[
            ParamDef("cdp_url", "string", "", "CDP 连接地址", flag="--cdp-url"),
            ParamDef("output", "string", "", "输出 JSON 文件路径", flag="-o"),
            ParamDef("export_sub2api", "boolean", False, "导出 sub2api 兼容格式", is_flag=True, flag="--export-sub2api"),
            ParamDef("export_sub2api_output", "string", "", "sub2api 导出文件路径", flag="--export-sub2api-output"),
            ParamDef("pretty", "boolean", False, "美化打印", is_flag=True),
            ParamDef("api_keys_only", "boolean", False, "只读取 API Keys", is_flag=True, flag="--api-keys-only"),
            ParamDef("user_only", "boolean", False, "只读取用户信息", is_flag=True, flag="--user-only"),
            ParamDef("create_key", "string", None, "若不存在 API Key 则自动创建"),
            ParamDef("yes", "boolean", False, "跳过敏感操作确认", is_flag=True, flag="--yes"),
        ],
    ),
    CommandDef(
        name="account-status",
        group="status",
        description="""诊断 zenmux 账号当前状态。""",
        handler="zm_auto.cli.account_status:main",
        params=[
            ParamDef("cdp_url", "string", "", "CDP 连接地址", flag="--cdp-url"),
        ],
    ),
    CommandDef(
        name="doctor",
        group="diag",
        description="""输出环境、配置、provider 与 CDP 状态。""",
        handler="zm_auto.cli.doctor:main",
        params=[
            ParamDef("format", "string", "text", "输出格式 (text|json)", flag="--format"),
            ParamDef("compact", "boolean", False, "紧凑输出，适合 Agent 解析", is_flag=True, flag="--compact"),
        ],
    ),
    CommandDef(
        name="skills",
        group="agent",
        description="""导出 AI Agent 可用的 CLI skill schema。""",
        handler="zm_auto.cli.skills:main",
        params=[
            ParamDef("format", "string", "json", "输出格式 (json|compact)", flag="--format"),
        ],
    ),
]


def get_command(name: str) -> CommandDef | None:
    """按命令名查找命令定义。"""
    for cmd in COMMANDS:
        if cmd.name == name:
            return cmd
    return None


def get_commands_by_group(group: str) -> list[CommandDef]:
    """按分组查找命令定义。"""
    return [cmd for cmd in COMMANDS if cmd.group == group]


def registry_json_schema() -> dict[str, Any]:
    """生成整个命令注册表的 JSON Schema。"""
    return {cmd.name: cmd.to_json_schema() for cmd in COMMANDS}
