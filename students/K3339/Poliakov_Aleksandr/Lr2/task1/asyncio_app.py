from __future__ import annotations

import argparse
import asyncio
import json
import time

from common_sum import DEFAULT_N, calculate_range_sum, split_range


async def calculate_sum(start: int, end: int, mode: str = "formula") -> int:
    if mode == "formula":
        await asyncio.sleep(0)
        return calculate_range_sum(start, end, mode)

    total = 0
    checkpoint = 200_000
    for index, value in enumerate(range(start, end + 1), start=1):
        total += value
        if index % checkpoint == 0:
            await asyncio.sleep(0)
    return total


async def run_async(n: int, workers: int, mode: str) -> tuple[int, float]:
    ranges = split_range(1, n, workers)
    started_at = time.perf_counter()
    tasks = [calculate_sum(part.start, part.end, mode) for part in ranges]
    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - started_at
    return sum(results), elapsed


def run(n: int, workers: int, mode: str) -> tuple[int, float]:
    return asyncio.run(run_async(n, workers, mode))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Task 1: sum with asyncio")
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--mode", choices=("formula", "loop"), default="formula")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result, elapsed = run(args.n, args.workers, args.mode)
    payload = {
        "approach": "asyncio",
        "n": args.n,
        "workers": args.workers,
        "mode": args.mode,
        "result": result,
        "seconds": elapsed,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"Approach: asyncio")
        print(f"N: {args.n}")
        print(f"Workers: {args.workers}")
        print(f"Mode: {args.mode}")
        print(f"Result: {result}")
        print(f"Time: {elapsed:.6f} sec")


if __name__ == "__main__":
    main()
