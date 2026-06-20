"""Core Registrar class implementation."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import json
import threading
import time
from datetime import datetime
from pathlib import Path

import urllib3

from zm_auto.config import load_config
from zm_auto.constants import BASE_DIR, USER_AGENT, X_API_VERSION
from zm_auto.sites import get_site_adapter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {"done": 0, "success": 0, "fail": 0, "start_time": 0.0}

config = load_config().model_dump()


def _target_base() -> str:
    """Return the configured target site base URL via site adapter."""
    return str(get_site_adapter().site_url).rstrip("/")


# Backward-compatible module-level constants (resolved at import time).
TARGET_BASE = _target_base()
API_BASE = f"{TARGET_BASE}/api"


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def log(text: str, color: str = "") -> None:
    colors = {"red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m", "cyan": "\033[36m"}
    with print_lock:
        prefix = colors.get(color, "")
        suffix = "\033[0m" if prefix else ""
        logger.info(f"{prefix}{datetime.now().strftime('%H:%M:%S')} {text}{suffix}")


def step(index: int, text: str, color: str = "") -> None:
    log(f"[任务{index}] {text}", color)


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def _api_headers(referer: str = "") -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "x-api-version": X_API_VERSION,
        "User-Agent": USER_AGENT,
    }
    if referer:
        headers["Referer"] = referer
    return headers


def worker(index: int) -> dict:
    from zm_auto.services.registrar_class import Registrar
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


def run(total: int | None = None, threads: int | None = None) -> list[dict]:
    total = total if total is not None else config.get("total", 1)
    threads = threads if threads is not None else config.get("threads", 1)
    threads = max(1, min(threads, total))

    stats["start_time"] = time.time()
    log(f"开始注册 {total} 个账号，并发 {threads}", "cyan")

    results: list[dict] = []
    if threads == 1:
        for i in range(1, total + 1):
            results.append(worker(i))
    else:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=threads) as pool:
            futures = {pool.submit(worker, i): i for i in range(1, total + 1)}
            for future in as_completed(futures):
                results.append(future.result())

    elapsed = time.time() - stats["start_time"]
    success = sum(1 for r in results if r.get("ok"))
    log(
        f"完成: {success}/{total} 成功，{total - success} 失败，总耗时 {elapsed:.1f}s",
        "green" if success == total else "yellow",
    )

    save_results(results)
    return results


def save_results(results: list[dict]) -> Path:
    out_file = BASE_DIR / "accounts.json"
    existing: list = []
    if out_file.exists():
        try:
            existing = json.loads(out_file.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []
    for r in results:
        if r.get("ok") and r.get("result"):
            existing.append(r["result"])
    out_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"结果已保存到 {out_file}", "cyan")
    return out_file


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="自动注册机 (纯 HTTP + 2captcha / 浏览器)")
    parser.add_argument("-n", "--total", type=int, help="注册数量")
    parser.add_argument("-t", "--threads", type=int, help="并发数")
    parser.add_argument("--proxy", type=str, help="代理地址")
    args = parser.parse_args()

    if args.total is not None:
        config["total"] = args.total
    if args.threads is not None:
        config["threads"] = args.threads
    if args.proxy is not None:
        config["proxy"] = args.proxy

    run(total=config.get("total", 1), threads=config.get("threads", 1))


if __name__ == "__main__":
    main()
