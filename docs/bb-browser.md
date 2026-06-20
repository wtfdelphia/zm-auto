---

# 🔍 bb-browser 项目全面分析

## 📋 项目概览

| 属性 | 详情 |
|------|------|
| **名称** | `bb-browser`（BadBoy Browser） |
| **口号** | *"Your browser is the API. No keys. No bots. No scrapers."* |
| **版本** | v0.14.2 |
| **作者** | [epiral](https://github.com/epiral)（核心开发者 yan5xu / Yanwu） |
| **许可证** | MIT |
| **语言** | TypeScript（主体）+ Go（bb-viewer 视频流组件） |
| **运行时** | Node.js ≥ 18 |
| **包管理** | pnpm 9 + Turborepo（monorepo） |
| **npm 包** | `bb-browser` |
| **首次提交** | ~2026 年 2 月（约 4 个月历史） |
| **发布版本** | 15 个 tag（v0.5.2 → v0.14.0），迭代极为频繁 |

---

## 🎯 核心定位

bb-browser 的核心理念极其精炼：

> **你的浏览器就是 API。** AI Agent 不需要 API Key、不需要爬虫、不需要逆向工程——它直接使用你已经登录的 Chrome 浏览器来访问互联网。

传统 AI Agent 的世界是 `文件 + 终端 + 少数有 API Key 的服务`。有了 bb-browser，Agent 的世界变成了 `文件 + 终端 + 整个互联网`。

---

## 🏗️ 技术架构

### 架构图

```
AI Agent (Claude Code, Codex, Cursor, etc.)
       │ CLI or MCP (stdio)
       ▼
bb-browser CLI ──HTTP──▶ Daemon ──CDP WebSocket──▶ Your Real Chrome
                           │
                    ┌──────┴──────┐
                    │ Per-tab     │
                    │ event cache │
                    │ (network,   │
                    │  console,   │
                    │  errors)    │
                    └─────────────┘
                           │
                    ┌──────┴──────┐ (可选 Hub 模式)
                    │ Hub Bridge  │──▶ Pinix Hub (远程访问)
                    │ + Streamer  │──▶ WebRTC 视频流
                    │ (bb-viewer) │
                    └─────────────┘
```

### 三根 CDP 连接

| 连接 | Owner | 职责 |
|------|-------|------|
| **controlConn** | daemon | Agent 操作：tab/导航/site/DOM/click |
| **inputConn** | streamer | 人类实时输入：鼠标/键盘/IME |
| **captureConn** | streamer | 视频流：screencast → VP8 → WebRTC |

### Monorepo 结构

```
bb-browser/
├── packages/
│   ├── cli/          # CLI 命令行入口
│   ├── daemon/       # 核心守护进程（CDP 控制、HTTP API、Hub 连接）
│   └── shared/       # 统一命令定义、协议类型
├── web/
│   └── view.html     # 远程浏览器 Web UI（35KB 单文件应用）
├── skills/           # AI Agent 技能定义
│   ├── bb-browser/
│   └── bb-browser-openclaw/
├── Dockerfile        # Docker 部署（Xvfb + headed Chrome）
├── AGENTS.md         # Agent 开发规范（8.6KB，极其详细）
├── PRIVACY.md        # 隐私政策
├── CHANGELOG.md      # 变更日志（35KB，非常详尽）
├── turbo.json        # Turborepo 配置
├── tsup.config.ts    # 构建配置
└── pnpm-workspace.yaml
```

### 技术栈

| 层级 | 技术 |
|------|------|
| **CLI 框架** | 自研命令解析（基于 shared/commands.ts 统一定义） |
| **浏览器控制** | Chrome DevTools Protocol (CDP) 直连 |
| **守护进程** | Node.js HTTP Server（`127.0.0.1:19824`） |
| **视频流** | bb-viewer（Go binary，libvpx + libturbojpeg，WebRTC via Pion） |
| **远程访问** | Pinix Hub（Connect-RPC ProviderStream） |
| **TURN 中继** | coturn（动态凭证从 Hub API 获取） |
| **构建** | tsup + Turborepo + pnpm |
| **代码质量** | ESLint 9 + Husky + release-please |
| **容器化** | Docker（Xvfb + headed Chrome，反反爬） |
| **RPC** | `@connectrpc/connect` + `@bufbuild/protobuf` |

---

## 🔧 功能矩阵

### 浏览器自动化命令

| 组 | 命令 | 说明 |
|----|------|------|
| **导航** | `open`, `goto`, `back`, `forward`, `reload`, `close` | URL 导航与 tab 内导航 |
| **观察** | `snap`, `screenshot`, `get`, `eval` | 无障碍树快照、截图、JS 执行 |
| **交互** | `click`, `hover`, `fill`, `type`, `press`, `scroll`, `check`, `uncheck`, `select` | 完整 DOM 交互 |
| **Tab** | `tab list`, `tab new`, `tab select`, `tab close` | 多 Tab 并发隔离 |
| **调试** | `network`, `console`, `errors`, `trace`, `cookies`, `source` | 网络抓包、JS 源码搜索、操作录制 |
| **进程** | `daemon start/stop/status` | 守护进程管理 |

### Site Adapter 系统（36 平台，103 命令）

| 类别 | 平台 | 命令数 |
|------|------|--------|
| **搜索** | Google, Baidu, Bing, DuckDuckGo, 搜狗微信 | search |
| **社交** | Twitter/X, Reddit, 微博, 小红书, 即刻, LinkedIn, 虎扑 | search, feed, thread, user, notifications, hot |
| **新闻** | BBC, Reuters, 36kr, 头条, 东方财富 | headlines, search, newsflash, hot |
| **开发** | GitHub, StackOverflow, HackerNews, CSDN, 博客园, V2EX, Dev.to, npm, PyPI, arXiv | search, issues, repo, top, thread, package |
| **视频** | YouTube, Bilibili | search, video, transcript, popular, comments, feed |
| **影视** | 豆瓣, IMDb, Genius, 起点 | movie, search, top250 |
| **金融** | 雪球, 东方财富, Yahoo Finance | stock, hot stocks, feed, watchlist, search |
| **招聘** | BOSS 直聘, LinkedIn | search, detail, profile |
| **知识** | Wikipedia, 知乎, Open Library | search, summary, hot, question |
| **购物** | 什么值得买 | search deals |
| **工具** | 有道, GSMArena, Product Hunt, 携程 | translate, phone specs, trending |

Adapter 来自社区仓库 [bb-sites](https://github.com/epiral/bb-sites)，每个命令一个 JS 文件，三级复杂度：

| 级别 | 认证方式 | 示例 | 耗时 |
|------|----------|------|------|
| **Tier 1** | Cookie（直接 fetch） | Reddit, GitHub, V2EX | ~1 分钟 |
| **Tier 2** | Bearer + CSRF Token | Twitter, 知乎 | ~3 分钟 |
| **Tier 3** | Webpack 注入 / Pinia Store | Twitter 搜索, 小红书 | ~10 分钟 |

---

## 🔐 安全与隐私模型

| 特性 | 说明 |
|------|------|
| **全本地通信** | CLI ↔ localhost:19824 (daemon) ↔ Chrome，无外部服务器 |
| **无遥测** | 零 analytics、零 telemetry |
| **无数据持久化** | 所有数据仅在内存中，tab 关闭即清除 |
| **TURN 凭证** | 动态获取（24h TTL），secret 仅在服务端 |
| **反反爬策略** | 不使用 stealth 注入（Google 检测 CDP domain 调用），使用裸 CDP + headed Chrome |
| **Docker 安全** | Xvfb 虚拟帧缓冲 + headed Chrome，避免 headless 检测 |

---

## 📊 项目活跃度

### 版本演进时间线

| 版本 | 日期 | 里程碑 |
|------|------|--------|
| v0.5.x | ~2026-02 | 初始版本，Chrome Extension 架构 |
| v0.8.0 | ~2026-03 | **架构大迁移**：Extension → CDP 直连 |
| v0.9.0 | 2026-03-19 | MCP Server、Site Adapter、OpenClaw 集成 |
| v0.11.0 | ~2026-04 | 统一命令注册、Chrome Extension 移除（Breaking） |
| v0.12.0 | ~2026-05 | Docker 支持、远程浏览器查看 |
| v0.13.0 | 2026-05-26 | TURN 内置、eval domain 路由 |
| v0.14.0 | 2026-05-28 | Trace 时间线、goto/cookies/source、Site adapter 迁移到 Hub |

### 提交活跃度

- **最新提交**：2026-05-29（`docs: update AGENTS.md`）
- **核心开发者**：yan5xu（几乎全部提交）
- **外部贡献者**：~5-8 人提交了 PR，部分由 AI Agent（Claude Code / Codex）生成
- **PR 总数**：~236 个（含 open 和 closed）

### Issues（63 个 Open）

关键问题：

| Issue | 类型 | 说明 |
|-------|------|------|
| #235 | 🔴 Bug | `--mcp` 参数在 0.14.2 中未实现（README 文档了但代码未打包） |
| #233 | 📝 Docs | MCP 移除后文档未同步更新 |
| #228 | 💡 Feature | Windows 完整支持（daemon + bb-viewer） |
| #217 | 🔴 Bug | 默认端口 19824 与 Windows IP Helper 冲突 |
| #215 | 🔴 Bug | ClaudeCode MCP 连接失败 |
| #201 | 🔴 Bug | Windows 上 MCP 模式立即退出 |
| #205 | 💡 Feature | WSL2 连接 Windows Chrome |
| #195 | 🔴 Bug | Tab ID 在 `--tab` 参数中无法正确使用 |

---

## 💡 设计亮点

### 1. "你的浏览器就是 API" 范式

这是项目最核心的创新。不同于 Playwright/Selenium 使用无头浏览器（无登录态），也不同于爬虫库（需要逆向 Cookie），bb-browser 直接使用你正在使用的 Chrome——网站认为就是你本人在操作。

### 2. 社区驱动的 Adapter 生态

通过 [bb-sites](https://github.com/epiral/bb-sites) 仓库，每个网站适配器只是一个 JS 文件。项目声称测试了 **20 个 AI Agent 并行运行，各自独立逆向一个网站并产出可用适配器**，将"添加新网站"的边际成本推向零。

### 3. Trace 时间线系统

将命令操作、人类浏览器操作、网络请求/响应统一录制到一条时间线上，并自动推断因果关系（`triggerSeq`）。这对逆向网站 API 和创建新 adapter 极为有用。

### 4. Docker 反反爬设计

在 Docker 中使用 Xvfb 虚拟帧缓冲运行 headed Chrome（而非 `--headless=new`），因为 Linux 上 headless 模式会跳过 X11/Ozone 显示层，导致 WebGL、`navigator.plugins` 等 API 返回异常值，被反自动化系统检测。

### 5. 远程浏览器查看

通过 bb-viewer（Go binary）+ WebRTC 实现远程实时查看和控制 Chrome，支持 P2P 直连和 TURN 中继回退。Clip Web UI 提供 Tab 栏、URL 栏、调试面板。

### 6. AGENTS.md 规范

8.6KB 的 Agent 开发规范，详细描述了架构、协议、设计不变量、代码规范，是 AI Agent 参与项目开发的"操作手册"。

---

## ⚠️ 风险与不足

| 风险 | 说明 |
|------|------|
| **MCP 功能缺失** | README 文档化了 `--mcp`，但 0.14.2 版本中 MCP 实现已被移除且未打包（Issue #235） |
| **文档与代码不同步** | 多次架构变更后，README、PRIVACY.md、Issue 模板仍引用已移除的 MCP/Extension 功能 |
| **Windows 支持薄弱** | 端口冲突（#217）、MCP 模式崩溃（#201）、Tab ID 失效（#195）等多个 Windows 特有 Bug |
| **单人核心开发** | yan5xu 贡献了绝大多数代码，项目可持续性依赖个人 |
| **架构频繁变更** | 4 个月内经历了 Extension → CDP 直连 → Hub 模式三次大架构迁移 |
| **bb-viewer 依赖** | Go binary 需要 CGo + libvpx + libturbojpeg，跨平台编译复杂 |
| **Pinix Hub 耦合** | 远程访问和 TURN 凭证依赖 Pinix Hub 服务，增加了外部依赖 |
| **Site Adapter 迁移中** | Adapter 正在从 daemon 本地扫描迁移到 Hub 上的独立 Bun Clips，过渡期可能不稳定 |
| **中文社区为主** | Issue 和 PR 大量中文，国际化程度有限 |

---

## 🆚 竞品对比

| 特性 | bb-browser | Playwright/Selenium | Browser Use | DevSpace |
|------|-----------|---------------------|-------------|----------|
| **浏览器** | 你的真实 Chrome | Headless 隔离实例 | Headless | 不涉及浏览器 |
| **登录态** | ✅ 已有 | ❌ 需重新登录 | ❌ 需重新登录 | N/A |
| **反爬检测** | 不可见（就是用户） | 容易被检测 | 容易被检测 | N/A |
| **API Key** | 不需要 | 不需要 | 不需要 | 不需要 |
| **MCP 支持** | ~~已移除~~ | 无 | 部分 | ✅ |
| **远程访问** | ✅ WebRTC | 无 | 无 | ✅ 隧道 |
| **社区 Adapter** | 36 平台 103 命令 | 无 | 无 | 无 |
| **视频流** | ✅ WebRTC | 无 | 无 | 无 |

---

## 📈 总结评价

**bb-browser 是一个极具创意和野心的项目**，它精准地抓住了 AI Agent 时代的一个核心痛点：99% 的网站没有 API，而 AI Agent 需要访问互联网。通过"让机器直接使用人类的浏览器"这一范式，它优雅地解决了登录态、反爬、复杂认证等问题。

项目的工程质量较高：monorepo 结构清晰、CHANGELOG 详尽（35KB）、AGENTS.md 规范完善、Docker 部署考虑了反反爬细节、release-please 自动化发布。迭代速度极快（4 个月 15 个版本，3 次架构迁移），但也带来了文档与代码不同步的问题。

**适合人群**：
- 需要 AI Agent 访问需要登录的网站/服务的开发者
- 构建 AI 驱动的网页数据采集/研究工具
- 对 AI Agent 互联网访问能力有需求的团队
- Pinix / OpenClaw 生态用户

**建议关注**：MCP 功能的重新实现（#235）、Windows 兼容性修复、文档清理（#233），以及 Site Adapter 从本地到 Hub 的迁移进展。项目仍处于快速演进的早期阶段，生产环境使用需锁定版本并关注 Breaking Changes。