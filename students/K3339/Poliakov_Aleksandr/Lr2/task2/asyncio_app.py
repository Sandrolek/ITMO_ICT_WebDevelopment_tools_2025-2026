from __future__ import annotations

import argparse
import asyncio
import json
import time

import aiohttp

from db import dispose_async_engine, init_db_async, save_page_async
from html_title_parser import extract_title
from web_config import DEFAULT_URLS, USER_AGENT


def split_list(values: list[str], parts: int) -> list[list[str]]:
    if parts <= 0:
        raise ValueError("parts must be positive")
    return [values[index::parts] for index in range(parts) if values[index::parts]]


async def fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
        response.raise_for_status()
        return await response.text(errors="replace")


async def parse_and_save(url: str, session: aiohttp.ClientSession) -> dict[str, str]:
    html = await fetch_html(session, url)
    title = extract_title(html)
    await save_page_async(url, title, "asyncio")
    print(f"[asyncio] {url} -> {title}")
    return {"url": url, "title": title}


async def worker(
    urls: list[str],
    session: aiohttp.ClientSession,
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for url in urls:
        try:
            result = await parse_and_save(url, session)
        except Exception as exc:
            result = {"url": url, "title": f"ERROR: {exc}"}
            print(f"[asyncio] {url} -> ERROR: {exc}")
        results.append(result)
    return results


async def run_async(urls: list[str], workers: int) -> tuple[list[dict[str, str]], float]:
    await init_db_async()
    chunks = split_list(urls, workers)
    headers = {"User-Agent": USER_AGENT}

    started_at = time.perf_counter()
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            nested_results = await asyncio.gather(
                *(worker(chunk, session) for chunk in chunks)
            )
        elapsed = time.perf_counter() - started_at
    finally:
        await dispose_async_engine()

    results = [item for chunk in nested_results for item in chunk]
    return results, elapsed


def run(urls: list[str], workers: int) -> tuple[list[dict[str, str]], float]:
    return asyncio.run(run_async(urls, workers))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Task 2: web parsing with asyncio and aiohttp")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--url", action="append", dest="urls")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    urls = args.urls or DEFAULT_URLS
    results, elapsed = run(urls, args.workers)
    payload = {
        "approach": "asyncio",
        "workers": args.workers,
        "url_count": len(urls),
        "saved_count": len(results),
        "seconds": elapsed,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"Approach: asyncio")
        print(f"Workers: {args.workers}")
        print(f"URLs: {len(urls)}")
        print(f"Saved rows: {len(results)}")
        print(f"Time: {elapsed:.6f} sec")


if __name__ == "__main__":
    main()
