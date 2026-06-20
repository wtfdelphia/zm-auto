# Mail Provider 文档

`zm_auto/providers/` 抽象了 7 种临时邮箱 provider，统一通过 `create_mailbox()` 和 `wait_for_code()` 调用。

## 架构

```
zm_auto/providers/
  base.py           # BaseMailProvider 抽象类 + 自动注册
  cloudflare.py     # cloudflare_temp_email
  gptmail.py        # gptmail
  tempmail_lol.py   # tempmail_lol
  duckmail.py       # duckmail
  moemail.py        # moemail
  inbucket.py       # inbucket
  yyds.py           # yyds_mail
```

## 自动注册

每个 provider 继承 `BaseMailProvider` 时，基类的 `__init_subclass__` 会自动将其注册到全局注册表。新增 provider 只需：

1. 新建文件继承 `BaseMailProvider`
2. 设置 `type` 和 `required_fields` 类属性
3. 实现 `create()` 和 `fetch_latest_message()`

## Provider 列表

| type | 说明 | 必填字段 |
|---|---|---|
| `cloudflare_temp_email` | Cloudflare Workers 自建 | `api_base`, `admin_password`, `domain` |
| `gptmail` | GPTMail 第三方服务 | `api_key` |
| `tempmail_lol` | TempMail.lol API v2 | `api_key`(可选), `domain`(可选) |
| `duckmail` | DuckMail | `api_key`, `default_domain` |
| `moemail` | MoEmail 自建 | `api_base`, `api_key`, `domain` |
| `inbucket` | Inbucket 自建 | `api_base`, `domain` |
| `yyds_mail` | YYDSMail | `api_base`, `api_key`, `domain` |

## 失败策略

- 域名失效：配置多个 `domain`，系统会轮询使用
- 验证码超时：受 `mail.wait_timeout` 和 `mail.wait_interval` 控制
- API 异常：provider 内部捕获并返回 `None`，上层可重试或切换下一个 provider

## 使用示例

```python
from zm_auto.providers import create_mailbox

provider = create_mailbox("gptmail", {"api_key": "xxx"})
mailbox = provider.create()
code = provider.wait_for_code(mailbox)
```
