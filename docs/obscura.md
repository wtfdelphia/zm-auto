---

# 🔍 Obscura 项目全面分析

## 📋 项目概览

| 属性 | 详情 |
|------|------|
| **名称** | Obscura |
| **口号** | *"The open-source headless browser for AI agents and web scraping"* |
| **版本** | v0.1.8（最新 tag） |
| **作者** | [h4ckf0r0day](https://github.com/h4ckf0r0day)（核心维护者 Gabriel / SGavrl） |
| **Stars** | ⭐ **10,000+**（README 中明确提到） |
| **许可证** | **Apache 2.0** |
| **语言** | **Rust**（嵌入 V8 引擎） |
| **运行时** | Rust 1.75+，V8（从源码编译） |
| **创建时间** | ~2026 年初（约 6 个月历史） |
| **平台** | Linux x86_64/ARM64, macOS ARM/x86_64, Windows |
| **Docker** | `h4ckf0r0day/obscura`（~57 MB 压缩，distroless） |

---

## 🎯 核心定位

Obscura 是一个**用 Rust 从零构建的无头浏览器引擎**，专为网页抓取和 AI Agent 自动化设计。它不是对 Chrome 的封装，而是一个独立的浏览器实现：

> **内嵌 V8 引擎运行真实 JavaScript，维护真实 DOM 树，支持 Chrome DevTools Protocol (CDP)，可作为 Puppeteer/Playwright 的 headless Chrome 替代品。**

核心卖点极其清晰——**比 headless Chrome 快 12 倍、内存占用少 6 倍**。

---

## 🏗️ 技术架构

### 性能对比（官方数据）

| 指标 | Obscura | Headless Chrome |
|------|---------|-----------------|
| **内存** | **30 MB** | 200+ MB |
| **二进制大小** | **70 MB** | 300+ MB |
| **反检测** | **内置** | 无 |
| **页面加载** | **85 ms** | ~500 ms |
| **启动时间** | **即时** | ~2s |
| **Puppeteer 兼容** | ✅ | ✅ |
| **Playwright 兼容** | ✅ | ✅ |

### Workspace 结构（8 个 crate）

```
obscura/
├── crates/
│   ├── obscura-cli/        # CLI 入口：fetch, serve, scrape, mcp
│   ├── obscura-cdp/        # Chrome DevTools Protocol WebSocket 服务器
│   ├── obscura-js/         # V8/deno_core 运行时 + JS/DOM shim
│   ├── obscura-dom/        # DOM 树实现 (tree.rs)
│   ├── obscura-net/        # HTTP 客户端 + stealth 客户端 + Cookie + 追踪器拦截
│   ├── obscura-browser/    # Page 类型、导航、JS 执行
│   ├── obscura-mcp/        # MCP (Model Context Protocol) 服务器
│   └── obscura/            # 可嵌入的 Rust 库 API
├── skills/                 # AI Agent 技能定义
├── docs/                   # 文档（GitBook）
├── assets/                 # 图标、赞助商 logo
├── Dockerfile              # 多阶段构建（distroless/cc，无 shell）
├── AGENTS.md               # AI Agent 开发规范（6.9KB）
├── Cargo.toml              # Workspace 配置
└── Cargo.lock              # 89KB（依赖锁定）
```

### 技术栈

| 层级 | 技术 |
|------|------|
| **JS 引擎** | V8（通过 `deno_core` 嵌入，从源码编译） |
| **DOM** | 自研 DOM 树（`obscura-dom`），基于 `html5ever` 解析 |
| **CSS 选择器** | `selectors` + `cssparser`（Servo 生态） |
| **网络** | `reqwest`（rustls-tls）+ `wreq`（stealth 模式，BoringSSL） |
| **WebSocket** | `tokio-tungstenite` |
| **异步运行时** | Tokio |
| **CLI** | `clap` 4 |
| **序列化** | `serde` + `serde_json` |
| **容器** | distroless/cc（无 shell、无包管理器） |
| **构建** | Cargo workspace + 多阶段 Docker |

### 架构依赖关系

```
obscura-cli
  ├── obscura-browser (Page, 导航)
  │     ├── obscura-js (V8 运行时, DOM shim)
  │     │     └── obscura-dom (DOM 树)
  │     └── obscura-net (HTTP, Cookie, Stealth)
  ├── obscura-cdp (CDP WebSocket)
  │     └── obscura-browser
  └── obscura-mcp (MCP 服务器)
        └── obscura-browser
```

---

## 🔧 功能矩阵

### CLI 命令

| 命令 | 说明 |
|------|------|
| `obscura fetch <URL>` | 获取并渲染单个页面（`--dump html/text/links/markdown/assets/original`） |
| `obscura serve --port 9222` | 启动 CDP WebSocket 服务器 |
| `obscura scrape <URL...>` | 多 URL 并行抓取（`--concurrency 25`） |
| `obscura mcp` | 启动 MCP 服务器（stdio / HTTP） |

### CDP 协议支持

| 域 | 方法 |
|----|------|
| **Target** | createTarget, closeTarget, attachToTarget, createBrowserContext |
| **Page** | navigate, getFrameTree, addScriptToEvaluateOnNewDocument, lifecycleEvents |
| **Runtime** | evaluate, callFunctionOn, getProperties, addBinding |
| **DOM** | getDocument, querySelector, querySelectorAll, getOuterHTML, resolveNode |
| **Network** | enable, setCookies, getCookies, setExtraHTTPHeaders, setUserAgentOverride, **getResponseBody** |
| **Fetch** | enable, continueRequest, fulfillRequest, failRequest（实时拦截） |
| **Storage** | getCookies, setCookies, deleteCookies |
| **Input** | dispatchMouseEvent, dispatchKeyEvent |
| **LP** | getMarkdown（DOM → Markdown 转换） |

### MCP 工具（12 个）

| 工具 | 说明 |
|------|------|
| `browser_navigate` | 导航到 URL |
| `browser_snapshot` | 返回页面 URL、标题、正文 |
| `browser_click` | CSS 选择器点击 |
| `browser_fill` | 设置输入框值 |
| `browser_type` | 追加文本 |
| `browser_press_key` | 键盘事件 |
| `browser_select_option` | 下拉选择 |
| `browser_evaluate` | JS 表达式执行 |
| `browser_wait_for` | 等待 CSS 选择器出现 |
| `browser_network_requests` | 列出网络请求 |
| `browser_console_messages` | 返回 console 消息 |
| `browser_close` | 关闭页面 |

### Stealth 模式（`--features stealth`）

| 能力 | 说明 |
|------|------|
| **指纹随机化** | GPU、屏幕、Canvas、Audio、Battery（每会话独立） |
| **UA 伪装** | `navigator.userAgentData`（Chrome 145，高熵值） |
| **事件信任** | `event.isTrusted` 正确区分（WeakSet 追踪，页面 JS 无法伪造） |
| **原生函数伪装** | `Function.prototype.toString()` → `[native code]` |
| **webdriver 隐藏** | `navigator.webdriver = undefined` |
| **追踪器拦截** | 3,520 个域名被拦截（分析、广告、遥测、指纹脚本） |
| **TLS 指纹** | BoringSSL（通过 `wreq` 客户端） |

---

## 🔐 安全与健壮性

### 防崩溃不变量

| 机制 | 说明 |
|------|------|
| **V8 终止看门狗** | 从独立线程终止卡住的 isolate（`arm_watchdog` / `disarm_watchdog`） |
| **进程级硬截止时间** | CLI 层面的绝对兜底 |
| **panic = "unwind"** | Release profile 固定为 unwind，`catch_unwind` 可捕获 panic |
| **DOM 操作 panic 安全** | `op_dom` 包裹在 `catch_unwind` 中，panic 返回 null 而非崩溃 |
| **DOM 循环引用防护** | `append_child` / `insert_before` 拒绝环（插入祖先节点为 no-op） |
| **SSRF 防护** | 默认阻止 loopback / RFC1918 / link-local 请求 |
| **Cookie 自管理** | 不使用 reqwest 的 cookie store，自建 CookieJar |

### 测试体系

| 测试 | 说明 |
|------|------|
| **cargo nextest** | 必须使用 nextest（每个测试独立进程，因为 V8 isolate 每进程一个） |
| **Obstacle Course** | 33 阶段行为测试（能力 + 速度），必须保持 33/33 |
| **WPT 一致性** | Web Platform Tests 子测试通过率 |
| **真实网站渲染语料库** | 实际网站渲染正确性验证 |

---

## 📊 项目活跃度

### 版本演进

| 版本 | 说明 |
|------|------|
| v0.1.0 | 初始发布 |
| v0.1.1 → v0.1.8 | 快速迭代（~6 个月内 9 个版本） |

### 近期提交（2026-06-13 至 06-18，5 天内）

| 提交 | 说明 |
|------|------|
| `docs: add AGENTS.md` | AI Agent 开发规范 |
| `js: add document.evaluate and XPathResult` | XPath 子集支持（Maps 抓取需要） |
| `cli: list fetch()/XHR resources in --dump assets` | 动态资源发现 |
| `js: make event.isTrusted false for page-constructed events` | 修复反检测漏洞 |
| `js: mark Event constructor as native` | 关闭指纹泄露向量 |
| `Add Network.getResponseBody support` | CDP 网络响应体获取 |
| `js: implement Element.getAttributeNames()` | 修复 Vue 3/Nuxt 水合 |
| `deps: drop unused reqwest cookies feature` | 修复 Windows 编译 |

### 贡献者

| 贡献者 | 角色 |
|--------|------|
| **SGavrl (Gabriel)** | 核心维护者，绝大多数提交 |
| **RohitMadhu** | XPath 兼容、Network.getResponseBody |
| **yzyf1312** | Event 构造函数 native 标记 |
| **johnnogueira** | `--dump cookies` PR（待审） |
| **charlesmamane26-sketch** | CI workflow PR（已关闭未合并） |

### Issues（2 个 Open）

| Issue | 类型 | 说明 |
|-------|------|------|
| #305 | 🔴 Bug | 抓取 scrape.center 失败（`Plugin is not defined`） |
| #42 | 💡 Feature | 添加 NixOS/nixpkgs 包 |

### Pull Requests

| PR | 状态 | 说明 |
|----|------|------|
| #313 | 🟢 Open | `--dump cookies` 导出 cookie jar 为 JSON |
| #312 | ✅ 已合并 | AGENTS.md |
| #311 | ✅ 已合并 | XPath 兼容 |
| #310 | ✅ 已合并 | fetch/XHR 资源列表 |
| #309 | ✅ 已合并 | event.isTrusted 修复 |
| #308 | 已关闭 | CI workflow（外部 PR，未合并） |
| #302 | ✅ 已合并 | Event native 标记 |
| #300 | ✅ 已合并 | Network.getResponseBody |
| #299 | ✅ 已合并 | Element.getAttributeNames() |
| #296 | ✅ 已合并 | 移除未使用的 reqwest cookies |

---

## 💡 设计亮点

### 1. Rust 原生性能

Obscura 不是 Electron/Node.js 套壳，而是用 Rust 从底层构建的浏览器引擎。30MB 内存 vs Chrome 的 200+MB，85ms 页面加载 vs 500ms——这对大规模抓取场景（数千并发）意味着巨大的成本节约。

### 2. V8 嵌入 + 真实 DOM

通过 `deno_core` 嵌入 V8 引擎，运行真实的 JavaScript。自研 DOM 树基于 Servo 生态的 `html5ever` + `selectors`，不是模拟——是真正的浏览器引擎。

### 3. CDP 兼容 = Puppeteer/Playwright 即插即用

完整的 Chrome DevTools Protocol 实现意味着现有的 Puppeteer/Playwright 代码可以零修改切换到 Obscura——只需改连接地址。

### 4. Stealth 模式的工程深度

- `event.isTrusted` 使用 closure-private WeakSet 追踪，页面 JS 无法读取或伪造
- CDP 输入管线通过 non-enumerable `__obscura_markTrusted` 标记自动化事件为 trusted
- Event 构造函数标记为 native，`toString()` 返回 `[native code]`
- BoringSSL TLS 指纹匹配真实浏览器

### 5. 健壮性工程

- V8 看门狗从独立线程终止卡住的 isolate
- DOM 操作 panic 安全（`catch_unwind` 包裹）
- DOM 循环引用防护（防止 `descendants()` 无限循环导致引擎挂起）
- SSRF 默认阻止私有网络地址

### 6. distroless Docker 镜像

基于 `gcr.io/distroless/cc-debian12`——无 shell、无包管理器，~57 MB 压缩。安全且极简。

---

## ⚠️ 风险与不足

| 风险 | 说明 |
|------|------|
| **V8 编译成本** | 首次构建需 ~5 分钟 + 数 GB 磁盘空间，从源码编译 V8 |
| **DOM 实现不完整** | 自研 DOM 树无法覆盖所有 Web API（如 XPath 仅支持子集，`Plugin` 未定义等） |
| **JS 兼容性问题** | 部分网站因缺失 API 而报错（Vue 3 水合、Maps XPath、Plugin 引用等） |
| **单人核心维护** | Gabriel (SGavrl) 贡献了绝大多数代码 |
| **外部 PR 选择性合并** | CI workflow PR (#308) 被关闭未合并 |
| **Stealth 依赖 BoringSSL** | stealth 模式需要 CMake 编译 BoringSSL，增加构建复杂度 |
| **不在 crates.io 上** | 嵌入库 `obscura` 仅支持 git 依赖，V8 本地编译 |
| **Obscura Cloud 尚未发布** | 商业版在 waitlist 阶段 |
| **测试限制** | 必须使用 `cargo nextest`，不能用标准 `cargo test` |
| **rustfmt 不兼容** | 代码树不是 rustfmt-clean 的，不能批量格式化 |

---

## 🆚 竞品对比

| 特性 | Obscura | Headless Chrome | Playwright | bb-browser | BrowserAct |
|------|---------|-----------------|------------|-----------|------------|
| **实现** | Rust 原生引擎 | Chromium 分支 | 封装 Chromium | CDP 客户端 | Python CLI |
| **内存** | **30 MB** | 200+ MB | 200+ MB | N/A | N/A |
| **启动** | **即时** | ~2s | ~2s | 需 daemon | 需 daemon |
| **反检测** | **内置** | 无 | 无 | 真实浏览器 | stealth 模式 |
| **CDP 兼容** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **MCP 支持** | ✅ | ❌ | ❌ | ~~已移除~~ | ❌ |
| **Puppeteer** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **并行抓取** | ✅ 原生 | 手动 | 手动 | ❌ | ✅ |
| **开源** | ✅ Apache 2.0 | ✅ BSD | ✅ Apache 2.0 | ✅ MIT | 部分 |
| **JS 引擎** | V8 (嵌入) | V8 (Chromium) | V8 (Chromium) | V8 (Chrome) | Chromium |
| **Docker 大小** | **~57 MB** | ~400 MB | ~400 MB | N/A | N/A |

---

## 📈 总结评价

**Obscura 是一个技术含量极高的项目**，它在浏览器自动化领域选择了一条最难但也最有价值的路线——**不用 Chromium，而是用 Rust 从零构建浏览器引擎**。

### 核心优势

1. **性能碾压**：30MB 内存、85ms 加载、即时启动——对大规模抓取场景（数千并发实例）意味着数倍的成本节约
2. **工程深度**：V8 嵌入、自研 DOM、CDP 完整实现、stealth 反检测——每一层都是硬核工程
3. **生态兼容**：Puppeteer/Playwright 即插即用 + MCP 原生支持——不要求用户改变工具链
4. **安全健壮**：看门狗、panic 安全、循环引用防护、SSRF 防护——生产级可靠性
5. **完全开源**：Apache 2.0，无功能门控，承诺永远如此

### 核心风险

1. **Web 兼容性**：自研 DOM 永远在追赶真实浏览器的 API 覆盖面，每个缺失的 API 都可能导致特定网站失败
2. **单人依赖**：核心维护者 Gabriel 一人承担了绝大多数开发
3. **V8 编译门槛**：从源码编译 V8 对贡献者和用户都设置了较高的入门门槛

### 适合人群

- **大规模网页抓取**：需要数千并发实例，内存和启动时间是核心成本
- **AI Agent 自动化**：需要 MCP 支持 + 反检测 + 轻量级浏览器
- **Puppeteer/Playwright 用户**：想零修改切换到更轻量的后端
- **安全敏感场景**：需要 distroless 容器 + SSRF 防护 + 无 shell 部署

### 商业前景

Obscura Cloud（托管版）正在 waitlist 阶段，结合开源引擎的 10K+ stars 和代理服务商赞助（5 家代理公司），商业模式清晰：**开源引擎获客 → 云服务变现**。这与 GitLab、Grafana 等成功开源商业化的路径一致。

**总体评价**：Obscura 是目前 AI Agent 浏览器自动化领域中**技术最硬核、性能最优、架构最干净的开源方案**。10K stars 的增长速度说明了社区对"轻量级反检测浏览器"这一需求的强烈渴望。如果 Web 兼容性能持续提升，它有潜力成为 headless Chrome 的真正替代品。