# Structure

## 目录结构

```
.
├── AGENTS.md                    # AI agent 本地规则
├── README.md                    # 项目入口文档
├── LICENSE
├── .gitignore
├── config.example.json          # 配置模板（无密钥）
├── config.json                  # 运行时配置（已忽略）
├── register.py                  # 注册主流程 / CLI
├── read_user_info.py            # 读取/导出已登录账号
├── mail_provider.py             # 临时邮箱 provider 抽象
├── captcha_solver.py            # 验证码求解器
├── cdp_solver.py                # CDP 人工介入验证码
├── check_account_status.py      # 账号状态检查
├── sub2api_importer.py          # sub2api 兼容导出
├── test.sh                      # 临时脚本 / 调试用（注意：不要提交密钥）
├── spec/                        # 长期事实源
│   ├── requirements.md
│   ├── design.md
│   └── structure.md
├── openspec/                    # OpenSpec 变更管理
│   ├── project.md
│   ├── specs/                   # 长期 capability facts
│   └── changes/                 # 单次变更过程
└── docs/                        # 参考文档 / 白皮书
```

## 源码结构说明

| 文件 | 职责 |
| --- | --- |
| `register.py` | 账号注册主流程、CLI、并发、结果持久化 |
| `read_user_info.py` | 读取用户/API Key、导出 sub2api |
| `mail_provider.py` | 7 种临时邮箱 provider 的封装 |
| `captcha_solver.py` | 验证码平台/浏览器/CDP 分发 |
| `cdp_solver.py` | CDP 连接与页面自动化 |
| `check_account_status.py` | 检查账号状态 |
| `sub2api_importer.py` | sub2api 格式导入/导出 |

## 配置与脚本归属

- 配置模板：`config.example.json`
- 运行时配置：`config.json`（不提交）
- 注册输出：`accounts.json`（不提交）
- 用户导出：`user_info.json`、`sub2api_export.json`（不提交）
- 调试脚本：`test.sh`（注意清理敏感信息）
