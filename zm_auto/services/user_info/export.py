from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import json
from datetime import datetime, timezone
from pathlib import Path

from zm_auto.config import load_config
from zm_auto.constants import BASE_DIR
from zm_auto.importers import Sub2APIImporter
from zm_auto.services.user_info.cdp_export import get_site_url
from zm_auto.services.user_info.cdp_export import _ts

def _build_model_mapping(models: list[str], model_aliases: dict[str, str] | None = None) -> dict[str, str]:
    """构建 model_mapping：配置模型映射到自己，并补充别名映射。

    model_aliases 优先于内置默认别名；若未提供则使用内置常见别名。
    """
    mapping: dict[str, str] = {m: m for m in models}
    if model_aliases:
        for alias, target in model_aliases.items():
            if alias not in mapping:
                mapping[alias] = target
    elif models:
        first = models[0]
        for alias in ("gpt-5.5", "gpt-5", "gpt-4", "claude-opus-4-7", "claude-sonnet-4"):
            if alias not in mapping:
                mapping[alias] = first
    return mapping

def _build_sub2api_export(
    api_keys: list[dict],
    user_info: dict | None,
    sub2api_cfg: dict,
) -> list[dict]:
    """将 API Keys 转换为 sub2api 兼容的账号导入格式。"""
    models = sub2api_cfg.get("models", [])
    export_cfg = sub2api_cfg.get("export", {})
    # base_url 从 export 配置读取，空则使用 site_url/api
    site_url = get_site_url()
    base_url = str(export_cfg.get("base_url") or f"{site_url}/api").rstrip("/")
    notes_path = str(export_cfg.get("notes_path", "/v1/chat/completions"))
    concurrency = int(export_cfg.get("concurrency", sub2api_cfg.get("concurrency", 3)))
    responses_supported = bool(export_cfg.get("openai_responses_supported", True))
    responses_mode = str(export_cfg.get("openai_responses_mode", "force_chat_completions"))

    model_mapping = _build_model_mapping(models, export_cfg.get("model_aliases", {}))

    accounts = []
    for key in api_keys:
        token = key.get("token") or key.get("key") or ""
        name = key.get("name", "")
        email = user_info.get("email", "") if user_info else ""

        accounts.append({
            "name": name or f"zenmux-{token[-6:]}" if token else "unknown",
            "notes": f"{base_url}{notes_path}",
            "platform": "openai",
            "type": "apikey",
            "credentials": {
                "api_key": token,
                "base_url": base_url,
                "model_mapping": model_mapping,
                "openai_capabilities": ["chat_completions"],
            },
            "extra": {
                "openai_apikey_responses_websockets_v2_enabled": False,
                "openai_apikey_responses_websockets_v2_mode": "off",
                "openai_compact_mode": "force_off",
                "openai_responses_mode": responses_mode,
                "openai_responses_supported": responses_supported,
            },
            "concurrency": concurrency,
            "priority": 51,
            "rate_multiplier": 1,
            "auto_pause_on_expired": True,
            # 附加元数据
            "source": "zenmux",
            "user_email": email,
            "user_id": user_info.get("userId", "") if user_info else "",
        })

    return accounts

def export_sub2api(result: dict, output_path: str = "") -> Path:
    """将 API Keys 导入 sub2api 服务器，并保存 JSON 记录。

    流程：读取 config.json sub2api 配置 → 调用 Sub2APIImporter 导入每个 key
    → 保存导入记录到 sub2api_export.json（数组，可追加，按 api_key 去重）。
    """
    cfg = load_config()
    sub2api_cfg = cfg.sub2api.model_dump()
    if not sub2api_cfg.get("enabled") and not sub2api_cfg.get("base_url"):
        logger.info(f"{_ts()} sub2api 未启用或未配置 base_url，仅导出 JSON")
        return _save_sub2api_json(result, output_path)

    api_keys = result.get("api_keys", [])
    user_info = result.get("user_info")

    if not api_keys:
        logger.info(f"{_ts()} ⚠ 没有 API Key 可导入")
        return Path()

    # 调用 Sub2APIImporter 真正导入
    importer = Sub2APIImporter(sub2api_cfg)
    imported: list[dict] = []
    failed: list[dict] = []

    for key in api_keys:
        token = key.get("token") or key.get("key") or ""
        name = key.get("name", "")
        email = user_info.get("email", "") if user_info else ""
        account_name = name or f"zenmux-{email.split('@')[0][:20]}" if email else f"zenmux-{token[-6:]}"

        try:
            account_data = importer.import_key(token, name=account_name)
            sub2api_id = account_data.get("id", "?")
            logger.info(f"{_ts()}   导入成功: {account_name} (sub2api id={sub2api_id})")
            export_cfg = sub2api_cfg.get("export", {})
            base_url = str(export_cfg.get("base_url") or f"{get_site_url()}/api").rstrip("/")
            notes_path = str(export_cfg.get("notes_path", "/v1/chat/completions"))
            concurrency = int(export_cfg.get("concurrency", sub2api_cfg.get("concurrency", 3)))
            responses_supported = bool(export_cfg.get("openai_responses_supported", True))
            responses_mode = str(export_cfg.get("openai_responses_mode", "force_chat_completions"))
            model_mapping = _build_model_mapping(sub2api_cfg.get("models", []), export_cfg.get("model_aliases", {}))

            imported.append(_build_import_record({
                "name": account_name,
                "notes": f"{base_url}{notes_path}",
                "platform": "openai",
                "type": "apikey",
                "credentials": {
                    "api_key": token,
                    "base_url": base_url,
                    "model_mapping": model_mapping,
                    "openai_capabilities": ["chat_completions"],
                },
                "extra": {
                    "openai_apikey_responses_websockets_v2_enabled": False,
                    "openai_apikey_responses_websockets_v2_mode": "off",
                    "openai_compact_mode": "force_off",
                    "openai_responses_mode": responses_mode,
                    "openai_responses_supported": responses_supported,
                },
                "concurrency": concurrency,
                "priority": 51,
                "rate_multiplier": 1,
                "auto_pause_on_expired": True,
                "source": "zenmux",
                "user_email": email,
                "user_id": user_info.get("userId", "") if user_info else "",
            }, sub2api_id))
        except Exception as e:
            logger.info(f"{_ts()}   导入失败: {account_name} — {e}")
            failed.append({"name": account_name, "credentials": {"api_key": token}, "error": str(e)})

    # 保存导入记录到 JSON（追加模式）
    out_path = Path(output_path) if output_path else (BASE_DIR / "sub2api_export.json")
    _append_json_records(out_path, imported)
    logger.info(f"{_ts()} sub2api 导入完成: 成功 {len(imported)}，失败 {len(failed)}，记录已保存到 {out_path}")
    return out_path

def _save_sub2api_json(result: dict, output_path: str = "") -> Path:
    """仅导出 JSON 记录（不调用 sub2api 服务器）。"""
    cfg = load_config()
    sub2api_cfg = cfg.sub2api.model_dump()
    api_keys = result.get("api_keys", [])
    user_info = result.get("user_info")
    accounts = _build_sub2api_export(api_keys, user_info, sub2api_cfg)
    out_path = Path(output_path) if output_path else (BASE_DIR / "sub2api_export.json")
    _append_json_records(out_path, accounts)
    logger.info(f"{_ts()} 仅导出 JSON: {out_path} ({len(accounts)} 个账号)")
    return out_path

def _build_import_record(account: dict, sub2api_id: str = "") -> dict:
    """将 sub2api 导入结果转为与 export 一致的记录格式。"""
    record = dict(account)
    record["imported_at"] = datetime.now(timezone.utc).isoformat()
    if sub2api_id:
        record["sub2api_id"] = sub2api_id
    return record

def _append_json_records(out_path: Path, new_records: list[dict]) -> None:
    """追加记录到 sub2api_export.json，按 api_key 去重。

    文件格式（sub2api 兼容导入格式）:
      {
        "exported_at": "2026-06-18T17:34:53Z",
        "proxies": [],
        "accounts": [account1, account2, ...]
      }
    """
    existing_accounts: list[dict] = []
    if out_path.exists():
        try:
            loaded = json.loads(out_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and "accounts" in loaded:
                existing_accounts = loaded.get("accounts", [])
            elif isinstance(loaded, list):
                # 兼容旧格式：纯数组
                existing_accounts = loaded
        except Exception:
            existing_accounts = []

    if not isinstance(existing_accounts, list):
        existing_accounts = []

    # 按 api_key 去重
    existing_keys = {a.get("credentials", {}).get("api_key", "") for a in existing_accounts}
    to_add = []
    for r in new_records:
        key = r.get("credentials", {}).get("api_key", "")
        if key and key not in existing_keys:
            to_add.append(r)
            existing_keys.add(key)

    existing_accounts.extend(to_add)

    # 输出 sub2api 兼容的导入格式
    export_data = {
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "proxies": [],
        "accounts": existing_accounts,
    }
    out_path.write_text(json.dumps(export_data, ensure_ascii=False, indent=2), encoding="utf-8")
