# CDP 模块

借鉴 bb-browser 的 `CdpConnection` 设计，把 Chrome DevTools Protocol 连接、target 发现、资源释放封装成 `CDPSession` 类。

## CDPSession

```python
from zm_auto.cdp.session import CDPSession

# 上下文管理器用法
with CDPSession("http://127.0.0.1:9222") as session:
    page = session.page
    page.goto("https://example.com")

# 手动管理（适用于需要跨方法保持连接的场景）
session = CDPSession("http://127.0.0.1:9222")
session.open()
try:
    page = session.page
finally:
    session.close()
```

## 启动 Chrome

```bash
open -a "Google Chrome" --args \
  --remote-debugging-port=9222 \
  --proxy-server="http://127.0.0.1:7890" \
  --user-data-dir=/tmp/chrome-cdp
```

## 资源安全

`CDPSession.close()` 按 page → browser → playwright 顺序关闭，忽略所有异常。`__del__` 中也会做最终清理，避免进程残留。
