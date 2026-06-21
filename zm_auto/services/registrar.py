"""Registrar service entry point."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from zm_auto.constants import BASE_DIR
from zm_auto.services.user_info.export import _save_sub2api_json
from zm_auto.services.registrar_class import Registrar
from zm_auto.services.registrar_core import (
    config,
    log,
    stats,
    stats_lock,
    step,
)


def worker(index: int, registrars: list | None = None) -> dict:
    start = time.time()
    registrar = Registrar(
        proxy=config.get("proxy", ""),
        captcha_cfg=config.get("captcha", {}),
    )
    if registrars is not None:
        registrars.append(registrar)
    try:
        step(index, "任务启动", "cyan")
        result = registrar.register(index)
        cost = time.time() - start
        with stats_lock:
            stats["done"] += 1
            stats["success"] += 1
            avg = (time.time() - stats["start_time"]) / max(stats["success"], 1)
        if result.get("api_key"):
            log(
                f'{result["email"]} 注册成功，耗时{cost:.1f}s，平均{avg:.1f}s/个，'
                f'API Key: {result["api_key"][:12]}...{result["api_key"][-4:]}',
                "green",
            )
        else:
            log(
                f'{result["email"]} 部分成功（API Key 未创建），耗时{cost:.1f}s，'
                f'原因: {result.get("note", "unknown")}',
                "yellow",
            )
        return {"ok": True, "index": index, "result": result}
    except Exception as e:
        cost = time.time() - start
        with stats_lock:
            stats["done"] += 1
            stats["fail"] += 1
        log(f"任务{index} 注册失败，耗时{cost:.1f}s，原因: {e}", "red")
        # 保存已获取的邮箱信息，方便排查
        partial = {
            "email": registrar.mailbox.get("address", ""),
            "email_provider": str(registrar.mailbox.get("provider") or ""),
            "email_token": str(registrar.mailbox.get("token") or ""),
            "api_key": "",
            "key_name": "",
            "note": "failed",
            "error": str(e),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return {"ok": False, "index": index, "error": str(e), "result": partial}
    finally:
        try:
            registrar.close()
        except Exception:
            pass


def run(total: int | None = None, threads: int | None = None, export_sub2api: bool = False, export_sub2api_output: str = "") -> Path:
    if total is None:
        total = int(config.get("total", 1))
    if threads is None:
        threads = int(config.get("threads", 1))
    threads = max(1, min(threads, total))

    stats["start_time"] = time.time()
    log(f"开始注册 {total} 个账号，并发 {threads}", "cyan")

    results: list[dict] = []
    registrars: list[Registrar] = []
    from concurrent.futures import ThreadPoolExecutor

    try:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(worker, i + 1, registrars) for i in range(total)]
            for future in futures:
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append({"ok": False, "error": str(e)})

        elapsed = time.time() - stats["start_time"]
        success = sum(1 for r in results if r.get("ok"))
        log(
            f"完成: {success}/{total} 成功，{total - success} 失败，总耗时 {elapsed:.1f}s",
            "green" if success == total else "yellow",
        )

        out_path = save_results(results)

        # 导出 sub2api 兼容格式（仅导出 JSON，不触发服务器导入）
        if export_sub2api:
            _export_sub2api_json(results, export_sub2api_output)

        return out_path
    finally:
        # CDP 浏览器退出登录放在文件写入之后，作为流程最后一步
        for registrar in registrars:
            try:
                registrar.logout()
            except Exception:
                pass


def save_results(results: list[dict]) -> Path:
    out_file = Path(BASE_DIR) / "accounts.json"
    existing: list[dict] = []
    if out_file.exists():
        try:
            existing = json.loads(out_file.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    for r in results:
        if r.get("result"):
            existing.append(r["result"])
    out_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"结果已保存到 {out_file}", "cyan")
    return out_file




def _export_sub2api_json(results: list[dict], output_path: str = "") -> None:
    """将注册结果追加导出到 sub2api_export.json。"""
    for r in results:
        if not r.get("ok") or "result" not in r:
            continue
        result = r["result"]
        email = result.get("email", "")
        user_id = result.get("user_id", "")
        api_key = result.get("api_key", "")
        key_name = result.get("key_name", "")
        if not api_key:
            continue
        export_result = {
            "api_keys": [{"name": key_name, "token": api_key}],
            "user_info": {"userId": user_id, "email": email},
        }
        _save_sub2api_json(export_result, output_path)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--total", type=int, default=int(config.get("total", 1)))
    parser.add_argument("-t", "--threads", type=int, default=int(config.get("threads", 1)))
    args = parser.parse_args()
    run(total=args.total, threads=args.threads)


if __name__ == "__main__":
    main()
