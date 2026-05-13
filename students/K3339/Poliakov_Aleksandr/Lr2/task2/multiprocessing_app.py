from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path
from urllib.request import Request, urlopen

from db import DEFAULT_DB_PATH, init_db, save_page
from html_title_parser import extract_title
from web_config import DEFAULT_URLS, USER_AGENT


def split_list(values: list[str], parts: int) -> list[list[str]]:
    if parts <= 0:
        raise ValueError("parts must be positive")
    return [values[index::parts] for index in range(parts) if values[index::parts]]


def fetch_html(url: str, timeout: int = 15) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_and_save(url: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, str]:
    html = fetch_html(url)
    title = extract_title(html)
    save_page(url, title, "multiprocessing", db_path)
    print(f"[multiprocessing] {url} -> {title}")
    return {"url": url, "title": title}


def worker_chunk(args: tuple[list[str], str]) -> list[dict[str, str]]:
    urls, db_path = args
    results: list[dict[str, str]] = []
    for url in urls:
        try:
            results.append(parse_and_save(url, db_path))
        except Exception as exc:
            result = {"url": url, "title": f"ERROR: {exc}"}
            print(f"[multiprocessing] {url} -> ERROR: {exc}")
            results.append(result)
    return results


def run(urls: list[str], workers: int, db_path: str | Path) -> tuple[list[dict[str, str]], float]:
    init_db(db_path)
    chunks = split_list(urls, workers)
    tasks = [(chunk, str(db_path)) for chunk in chunks]

    started_at = time.perf_counter()
    with mp.Pool(processes=workers) as pool:
        nested_results = pool.map(worker_chunk, tasks)
    elapsed = time.perf_counter() - started_at

    results = [item for chunk in nested_results for item in chunk]
    return results, elapsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Task 2: web parsing with multiprocessing")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--url", action="append", dest="urls")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    urls = args.urls or DEFAULT_URLS
    results, elapsed = run(urls, args.workers, args.db)
    payload = {
        "approach": "multiprocessing",
        "workers": args.workers,
        "url_count": len(urls),
        "saved_count": len(results),
        "seconds": elapsed,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"Approach: multiprocessing")
        print(f"Workers: {args.workers}")
        print(f"URLs: {len(urls)}")
        print(f"Saved rows: {len(results)}")
        print(f"Database: {args.db}")
        print(f"Time: {elapsed:.6f} sec")


if __name__ == "__main__":
    main()
