# 工具来源与版本口径

本文件记录 zm-auto 项目接入 AI 辅助开发工程化工作流所使用的工具来源、实际版本和用途。

## 核验口径

| 工具 | 来源 | 实际版本 / 验证日期 | 用途 | 不应提交 |
| --- | --- | --- | --- | --- |
| OpenSpec | https://github.com/Fission-AI/OpenSpec | `1.4.0`，2026-06-19 核验 | 规格驱动和变更归档 | token、本机缓存 |
| CodeGraph | https://github.com/colbymchenry/codegraph | `0.9.8`，2026-06-19 核验 | 本地代码图谱和影响面分析 | `.codegraph/` |
| ripgrep | https://github.com/BurntSushi/ripgrep | `15.1.0`，2026-06-19 核验 | 文本补盲 | 无 |
| Node.js | https://nodejs.org/ | `v24.14.1`，2026-06-19 核验 | OpenSpec / CodeGraph 运行时 | 无 |
| Python | https://python.org/ | `3.12.13`，2026-06-19 核验 | 项目主运行时 | 无 |
| uv | https://github.com/astral-sh/uv | `0.11.7`，2026-06-19 核验 | MCP server 运行时（fetch 等） | 无 |
| pytest | https://pytest.org/ | `9.1.1`，2026-06-19 核验 | 单元测试 | `.pytest_cache/`、`__pycache__/` |
| ECC | https://github.com/affaan-m/ECC | 未整包接入；仅按白皮书裁剪规则写入 `AGENTS.md` | rules / skills / agents 参考 | 用户级配置、密钥 |
| Karpathy skills | https://github.com/multica-ai/andrej-karpathy-skills | 行为纪律已本地化写入 `AGENTS.md` | 行为纪律 | 未裁剪外部配置 |

## 环境说明

- 本项目为纯 Python 脚本集合，OpenSpec 和 CodeGraph 通过 npm 全局安装。
- 企业网络、代理或镜像环境由每位开发者自行配置，不要把个人代理地址、账号或 token 写入项目文件。

## 项目验证命令

```bash
# 静态语法检查
python -m py_compile register.py read_user_info.py mail_provider.py captcha_solver.py cdp_solver.py check_account_status.py sub2api_importer.py

# OpenSpec 校验
openspec validate --all

# CodeGraph 索引状态
codegraph status

# CLI 帮助
python register.py --help
python read_user_info.py --help

# 单元测试（如有）
python -m pytest tests/ -v
```
