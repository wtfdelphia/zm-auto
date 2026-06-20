"""Registrar service entry point."""
from __future__ import annotations

import json
import time
from pathlib import Path

from zm_auto.constants import BASE_DIR
from zm_auto.services.registrar_class import Registrar
from zm_auto.services.registrar_core import (
    config,
    log,
    stats,
    stats_lock,
    step,
)


def worker(index: int) -> dict:
    start = time.time()
    registrar = Registrar(
        proxy=config.get("proxy", ""),
        captcha_cfg=config.get("captcha", {}),
    )
    try:
        step(index, "任务启动", "cyan")
        result = registrar.register(index)
        cost = time.time() - start
        with stats_lock:
            stats["done"] += 1
            stats["success"] += 1
            avg = (time.time() - stats["start_time"]) / max(stats["success"], 1)
        log(
            f'{result["email"]} 注册成功，耗时{cost:.1f}s，平均{avg:.1f}s/个，'
            f'API Key: {result["api_key"][:12]}...{result["api_key"][-4:]}',
            "green",
        )
        return {"ok": True, "index": index, "result": result}
    except Exception as e:
        cost = time.time() - start
        with stats_lock:
            stats["done"] += 1
            stats["fail"] += 1
        log(f"任务{index} 注册失败，耗时{cost:.1f}s，原因: {e}", "red")
        return {"ok": False, "index": index, "error": str(e)}
    finally:
        try:
            registrar.close()
        except Exception:
            pass


def run(total: int | None = None, threads: int | None = None) -> Path:
    if total is None:
        total = int(config.get("total", 1))
    if threads is None:
        threads = int(config.get("threads", 1))
    threads = max(1, min(threads, total))

    stats["start_time"] = time.time()
    log(f"开始注册 {total} 个账号，并发 {threads}", "cyan")

    results: list[dict] = []
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(worker, i + 1) for i in range(total)]
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

    return save_results(results)


def save_results(results: list[dict]) -> Path:
    out_file = Path(BASE_DIR) / "accounts.json"
    existing: list[dict] = []
    if out_file.exists():
        try:
            existing = json.loads(out_file.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    for r in results:
        if r.get("ok") and "result" in r:
            existing.append(r["result"])
    out_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"结果已保存到 {out_file}", "cyan")
    return out_file


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--total", type=int, default=int(config.get("total", 1)))
    parser.add_argument("-t", "--threads", type=int, default=int(config.get("threads", 1)))
    args = parser.parse_args()
    run(total=args.total, threads=args.threads)


if __name__ == "__main__":
    main()
