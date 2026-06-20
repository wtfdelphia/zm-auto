# Mail Providers

zm-auto 支持 7 种临时邮箱 provider，统一通过 `BaseMailProvider` 抽象。

## 注册与发现

借鉴 bb-browser 的 adapter 自动发现机制，每个 provider 继承 `BaseMailProvider` 并在 `__init_subclass__` 中自动注册，无需扫描文件或解析 docstring。

```python
from zm_auto.providers import BaseMailProvider, create_mailbox

class MyProvider(BaseMailProvider):
    type = "my_provider"
    required_fields = ["api_key"]

provider = create_mailbox("my_provider", {"api_key": "xxx"})
```

## Provider 列表

| Provider | Type | Required Fields |
|---|---|---|
| Cloudflare Temp Email | `cloudflare_temp_email` | `api_token`, `zone_id`, `email_name` |
| DuckMail | `duckmail` | - |
| GptMail | `gptmail` | - |
| Inbucket | `inbucket` | `host`, `port` |
| MoEmail | `moemail` | `api_base` |
| TempMail.lol | `tempmail_lol` | - |
| YYDS Mail | `yyds` | `api_base` |

## 失败策略

- 网络超时：按 `mail.wait_timeout` / `mail.wait_interval` 轮询
- 邮箱不可用：自动轮询下一个启用 provider
- 验证码未收到：抛 `RuntimeError`，由调用方决定是否重试
