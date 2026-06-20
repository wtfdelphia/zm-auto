---

# 🔍 BrowserAct Skills 项目全面分析

## 📋 项目概览

| 属性 | 详情 |
|------|------|
| **名称** | `browser-act/skills` |
| **口号** | *"Browser automation CLI built for AI agents"* |
| **版本** | CLI v0.1.27（`browser-act-cli`），Skill v2.0.2 |
| **组织** | [BrowserAct](https://www.browseract.com)（商业公司） |
| **许可证** | MIT（Skills 仓库），CLI 为商业产品 |
| **语言** | Python（CLI + 脚本），SKILL.md（Agent 指令） |
| **运行时** | Python 3.12+，uv 包管理器 |
| **Stars** | ⭐ **2,731** |
| **Forks** | 115 |
| **创建时间** | 2026-02-06（约 4.5 个月历史） |
| **平台** | Windows, macOS (ARM), Linux |
| **兼容 Agent** | Claude Code, Cursor, VS Code, OpenCode, OpenClaw, Codex, Gemini CLI |

---

## 🎯 核心定位

BrowserAct 是一个**面向 AI Agent 的浏览器自动化平台**，其核心差异化在于四个维度：

> **1. 突破反爬** — 三层递进防御（环境层 → 执行层 → 人类层）
> **2. 三种浏览器模式** — chrome（复用登录态）、stealth 隐私模式、stealth 固定身份
> **3. 零干扰并发** — 跨浏览器独立、同浏览器多会话、隐私模式零残留
> **4. 为 Agent 推理设计** — 紧凑文本输出、索引交互、语义记忆、并发安全

---

## 🏗️ 技术架构

### 架构总览

```
AI Agent (Claude Code / Cursor / Codex / ...)
       │ Shell 命令执行 + Skill 加载
       ▼
browser-act CLI ──HTTP──▶ BrowserAct 本地服务
       │                      │
       │                      ├──▶ Chrome 浏览器实例 (chrome / chrome-direct)
       │                      ├──▶ Stealth 浏览器实例 (反检测 Chromium)
       │                      └──▶ 代理服务 (Dynamic / Static / Custom)
       │
       ├── Skill 系统 (SKILL.md)
       ├── Skill Forge (自动生成爬虫 Skill)
       └── Solutions Catalog (30+ 预制 Skill)
```

### 仓库结构

```
browser-act/skills/
├── browser-act/
│   └── SKILL.md              # 核心 Skill 定义（3.8KB）
├── browser-act-skill-forge/
│   ├── SKILL.md              # Skill Forge 定义（19KB，极其详细）
│   └── references/           # 探索/生成参考文档
├── solutions/                # 30+ 预制 Skill 目录
│   ├── ecommerce/            # 19 个电商 Skill
│   ├── lead-generation/      # 11 个获客 Skill
│   ├── search-research/      # 5 个搜索研究 Skill
│   ├── social-listening/     # 20 个社交监听 Skill
│   └── video-platforms/      # 14 个视频平台 Skill
├── docs/                     # 12 篇详细文档
│   ├── anti-blocking.md      # 反爬三层防御
│   ├── browser-modes.md      # 浏览器模式详解
│   ├── concurrency.md        # 并发与隔离模型
│   ├── agent-design.md       # Agent 设计哲学
│   ├── skill-forge.md        # Skill Forge 文档
│   └── ...
├── .github/                  # CI/CD
├── requirements.txt          # Python 依赖
└── README.md                 # 项目主页
```

### 组织生态（4 个仓库）

| 仓库 | Stars | 说明 |
|------|-------|------|
| **skills** | 2,731 | 核心仓库：Skill 定义 + Solutions + 文档 |
| **browseract-workflow** | 18 | n8n 工作流集成 |
| **browseract-api-examples** | 16 | Python/Java/Node.js API 示例 |
| **claude-code-browser-act** | 13 | Claude Code 集成指南 |

---

## 🔧 核心功能矩阵

### 三层反爬防御

| 层级 | 解决什么 | 关键能力 |
|------|----------|----------|
| **环境层** | 让验证根本不触发 | 指纹伪装、TLS 轮换、住宅代理、隐私模式 |
| **执行层** | 触发后自动解决 | `solve-captcha` 自动验证码、`stealth-extract` 一键提取 |
| **人类层** | 自动化无法处理的情况 | `remote-assist` 远程接管（任何设备打开链接即可操作） |

### 三种浏览器模式

| 模式 | 场景 | 关键特性 |
|------|------|----------|
| **chrome** | 复用本地 Chrome 登录态 | Profile 导入 / CDP 直连，20+1 配额 |
| **stealth · 隐私模式** | 无需登录的批量抓取 | 每次会话新指纹 + 代理轮换，零残留 |
| **stealth · 固定身份** | 登录账户 · 多浏览器并行 | 稳定指纹 + 稳定 IP，不被标记为机器人 |

### 并发模型

| 模型 | 隔离级别 | 共享 | 典型用途 |
|------|----------|------|----------|
| **跨浏览器并行** | 浏览器级 | 无（独立指纹/IP/Cookie） | 多账户监控 |
| **同浏览器多会话** | 会话级 | 登录态 | 同账户并行任务 |
| **隐私模式零残留** | 会话级 | 无（每次全新） | 一次性采集 |

### 50+ CLI 命令

| 组 | 命令 |
|----|------|
| **浏览器管理** | `browser create/list/delete/update/import-profile` |
| **会话管理** | `session list/close` |
| **导航** | `browser open`, `back`, `forward`, `reload` |
| **状态观察** | `state`, `screenshot`, `eval` |
| **交互** | `click`, `input`, `select`, `upload`, `hover`, `press` |
| **数据提取** | `stealth-extract`, `network requests/har`, `cookies` |
| **安全** | `solve-captcha`, `remote-assist` |
| **代理** | `proxy list/buy-request` |
| **系统** | `get-skills`, `auth`, `report-log`, `feedback` |

---

## 🏭 Skill Forge — 核心创新

Skill Forge 是项目最具差异化的功能：**让 AI 自动为任何网站生成可复用的爬虫 Skill**。

### 四步流水线

```
描述需求 → 探索网站 → 生成 Skill 包 → 自动测试
```

| 步骤 | 说明 |
|------|------|
| **01 · 描述** | 用自然语言告诉 Agent 需要什么数据 |
| **02 · 探索** | API 优先（网络抓包发现端点），DOM 兜底 |
| **03 · 生成** | 参数化 Skill 包（SKILL.md + Python 脚本） |
| **04 · 自测** | 端到端验证 + 失败自修复 |

### SKILL.md 规范（19KB）

Skill Forge 的 SKILL.md 是我见过的最详细的 Agent 指令文件之一，包含：
- **Phase 0** — 工具检测
- **Phase 1** — 需求分析与确认（业务意图解析、目标站点研究、任务分解）
- **Phase 2** — 能力探索（API 优先、DOM 兜底、100 步探索上限）
- **Phase 3** — Skill 生成（JS 封装、封装验证、合规自检）
- **Delivery** — 自动测试 → 安装 → 报告 → 执行

### 效率规则

| 规则 | 说明 |
|------|------|
| **复合 eval** | 合并多个独立查询为一次 eval |
| **运行时优先** | JS 运行时状态 → 网络数据 → DOM |
| **输出量控制** | 在浏览器内提取关键字段，避免截断 |
| **验证即停** | API 端点确认有效后立即进入下一阶段 |

---

## 📦 Solutions Catalog（69 个预制 Skill）

| 类别 | 数量 | 覆盖平台 |
|------|------|----------|
| **电商** | 19 | Amazon (9), 淘宝 (4), 闲鱼 (2), 通用电商 (4) |
| **获客** | 11 | Google Maps (3), LinkedIn (2), GitHub, Indeed, Product Hunt, 社交媒体发现 (3) |
| **搜索研究** | 5 | Google (SERP/图片/新闻), 通用网页研究 |
| **社交监听** | 20 | Facebook (4), Instagram (5), Reddit (2), X/Twitter (3), 小红书 (4), 微信, 知乎 |
| **视频平台** | 14 | YouTube (10), TikTok (4) |

每个 Skill 包含：
- `SKILL.md` — Agent 指令文件
- `scripts/*.py` — Python 脚本（参数化）

---

## 💰 商业模式

| 功能 | 免费（无需注册） | 免费（需登录） | 付费 |
|------|:---:|:---:|:---:|
| 浏览器自动化（chrome / chrome-direct） | ✓ | ✓ | ✓ |
| Stealth 浏览器 (≤ 5)、stealth-extract、solve-captcha、remote-assist、隐私模式、Skill Forge | — | ✓ | ✓ |
| Stealth 浏览器 (> 5)、动态/静态代理 | — | — | ✓ |

**核心策略**：CLI 工具免费开源，通过代理服务和大规模 stealth 浏览器实例收费。

---

## 📊 项目活跃度

### 提交历史

- **最新提交**：2026-06-12（批量上传 xiaohongshu-auto-posting、x-keyword-comment、producthunt-launches、indeed-job-search 等 Skill）
- **提交模式**：大量批量上传 Skill（每个 Skill 3-5 个 commit），由 `browseract-skill` 账户统一提交
- **提交频率**：近期密集提交，主要集中在 Solutions Catalog 扩充

### Issues（2 个 Open）

| Issue | 类型 | 说明 |
|-------|------|------|
| #6 | 💡 Feature | 请求 macOS x86_64 (Intel) wheel 支持 |
| #4 | 💡 Feature | 请求云浏览器会话（持久登录 + 代理支持） |

### Pull Requests（2 个，均未合并）

| PR | 状态 | 说明 |
|----|------|------|
| #2 | 已关闭 | 文档：添加 TweetClaw 作为 X 社交监听伴侣 |
| #1 | 已关闭 | 代码整理：ruff、GitHub Actions、pyproject.toml |

**注意**：两个外部 PR 均被关闭未合并，说明项目对外部贡献的接受度较低，核心由团队控制。

---

## 💡 设计亮点

### 1. 为 LLM 推理设计的 CLI

- **紧凑索引文本**：比 JSON/HTML 节省数倍 token
- **索引交互**：`click 3` / `input 2 "hello"`，无需 DOM 解析
- **语义记忆**：每个浏览器带 `desc` 字段，Agent 按语义匹配任务

### 2. 确认门控（Confirmation Gating）

敏感操作（创建/删除浏览器、Profile 导入、代理变更）需要用户明确确认：
- 先前的批准不延续到新操作
- 每次敏感操作需要独立确认
- 用户原始提示中的肯定语言不替代确认

### 3. Skill Forge 的"探索一次，复用永远"

将"探索网站"和"使用网站"分离：
- 探索成本一次性支付
- 500 或 5000 条记录都走同一条稳定路径
- 网站改版时只需重新探索

### 4. 本地数据处理

所有数据留在本地：Cookie、登录会话、页面内容、截图、网络捕获、浏览器配置文件——**唯一例外**是 `solve-captcha` 发送验证码图片到云端。

---

## ⚠️ 风险与不足

| 风险 | 说明 |
|------|------|
| **闭源 CLI** | `browser-act-cli` 是 Cython 编译的二进制 wheel，源码不可审计 |
| **平台依赖** | 核心功能依赖 BrowserAct 商业服务（API Key、代理、stealth 浏览器） |
| **macOS Intel 不支持** | 仅提供 ARM64 wheel，Intel Mac 用户需 Docker 绕行（Issue #6） |
| **外部 PR 全拒** | 2 个外部 PR 均被关闭未合并，社区贡献通道不畅 |
| **单人提交** | 所有 commit 来自 `browseract-skill` 单一账户 |
| **Skill 质量未验证** | 69 个 Solutions 由 Skill Forge 自动生成，缺乏系统测试 |
| **确认门控依赖模型** | 安全机制依赖 LLM 遵循 Skill 指令，不同模型/平台执行程度不同 |
| **社交监听伦理** | X DM 自动聊天、X 关键词评论、小红书自动发帖等 Skill 存在滥用风险 |
| **无 MCP 支持** | 仅通过 Shell 命令与 Agent 交互，不支持 MCP 协议 |
| **文档中英混杂** | 部分文档和 commit message 中英混杂 |

---

## 🆚 竞品对比

| 特性 | BrowserAct | bb-browser | DevSpace | Playwright |
|------|-----------|-----------|----------|------------|
| **反爬能力** | ✅ 三层防御 | ✅ 真实浏览器 | ❌ 不涉及 | ❌ 易被检测 |
| **登录态复用** | ✅ 三种模式 | ✅ 你的 Chrome | ✅ 本地文件 | ❌ 需重新登录 |
| **远程人类接管** | ✅ remote-assist | ✅ WebRTC | ❌ | ❌ |
| **自动验证码** | ✅ solve-captcha | ❌ | ❌ | ❌ |
| **Skill 自动生成** | ✅ Skill Forge | ✅ 社区 Adapter | ❌ | ❌ |
| **预制 Skill 数** | 69 | 103 | 0 | 0 |
| **多账户隔离** | ✅ 浏览器级 | ❌ 单 Chrome | ❌ | 手动 |
| **代理服务** | ✅ 内置 | ❌ | ❌ | ❌ |
| **开源程度** | 部分（Skill 开源，CLI 闭源） | ✅ 完全开源 | ✅ 完全开源 | ✅ 完全开源 |
| **MCP 支持** | ❌ | ~~已移除~~ | ✅ | ❌ |
| **Stars** | 2,731 | ~未知 | ~未知 | 70K+ |
| **商业模式** | Freemium | 开源 + Hub 服务 | 开源 | 开源 (Microsoft) |

---

## 📈 总结评价

**BrowserAct Skills 是一个商业化程度高、产品思维强的 AI Agent 浏览器自动化平台。** 它在以下方面表现出色：

### 优势
1. **产品定位精准**：填补了"AI Agent 需要突破反爬、需要人类兜底、需要多账户隔离"的市场空白
2. **Skill Forge 创新**：将"探索网站"和"使用网站"分离，是爬虫工程化的新思路
3. **Agent-first 设计**：紧凑文本输出、索引交互、语义记忆——真正为 LLM 推理优化
4. **文档体系完善**：12 篇专题文档，覆盖反爬、并发、浏览器模式、Agent 设计哲学
5. **Solutions Catalog 丰富**：69 个预制 Skill 覆盖电商、获客、社交、视频等主流场景

### 劣势
1. **CLI 闭源**：核心 CLI 是 Cython 编译的二进制，用户无法审计代码
2. **商业依赖强**：stealth 浏览器、代理、验证码解决均需付费 API Key
3. **社区开放度低**：外部 PR 全部拒绝，社区贡献通道封闭
4. **伦理风险**：社交监听 Skill（自动 DM、关键词评论、自动发帖）存在被用于垃圾信息/操纵的风险

### 适合人群
- 需要大规模网页数据采集的企业/团队
- 构建 AI Agent 驱动的自动化工作流
- 电商竞品分析、社交监听、获客自动化
- 需要突破反爬 + 人类兜底的高可靠性场景

### 建议关注
- macOS Intel 支持（Issue #6）
- 云浏览器会话功能（Issue #4）
- Skill Forge 生成质量的系统性验证
- CLI 是否会开放源码审计

**总体评价**：这是一个**产品化程度高、但社区开放度低**的项目。它更像是一个商业产品的开源"前端"（Skill 层），而非真正的开源项目。对于需要其特定能力的用户来说，它是目前市场上最完善的 AI Agent 浏览器自动化方案之一；但对于追求完全开源和可审计性的用户来说，bb-browser 或 Playwright 可能是更透明的选择。