# GEMINI.md — Gemini 项目规则

## 项目上下文

- 项目名: zm-auto
- 定位: 全自动账号注册 + API Key 获取的 Python 工具集
- 入口脚本: `register.py`, `read_user_info.py`
- AI 通用规则: `AGENTS.md`
- 长期事实: `spec/`
- OpenSpec 变更: `openspec/changes/<change-name>/`

## 协作纪律

- 先读 `AGENTS.md` 再读 `GEMINI.md`。
- 新需求、跨模块改动、验证码/邮箱 provider 新增、CLI 参数变化、配置文件结构变化、输出格式变化，必须先建立 OpenSpec change。
- 不确定时列出假设，不静默猜测。
- 不提交 token、密码、Cookie、运行时输出。

## 验证要求

- 静态检查: `python3 -m py_compile *.py`
- CLI 帮助: `python3 register.py --help`, `python3 read_user_info.py --help`
- 冒烟验证: `python3 register.py -n 1`（需正确配置 `config.json`）
