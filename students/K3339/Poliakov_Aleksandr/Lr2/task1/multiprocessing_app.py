from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time

from common_sum import DEFAULT_N, RangePart, calculate_range_sum, split_range


def calculate_sum(start: int, end: int, mode: str = "formula") -> int:
    return calculate_range_sum(start, end, mode)


def worker(args: tuple[int, int, str]) -> int:
    start, end, mode = args
    return calculate_sum(start, end, mode)


def run(n: int, workers: int, mode: str) -> tuple[int, float]:
    ranges: list[RangePart] = split_range(1, n, workers)
    tasks = [(part.start, part.end, mode) for part in ranges]

    started_at = time.perf_counter()
    with mp.Pool(processes=workers) as pool:
        results = pool.map(worker, tasks)
    elapsed = time.perf_counter() - started_at

    return sum(results), elapsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Task 1: sum with multiprocessing")
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--mode", choices=("formula", "loop"), default="formula")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result, elapsed = run(args.n, args.workers, args.mode)
    payload = {
        "approach": "multiprocessing",
        "n": args.n,
        "workers": args.workers,
        "mode": args.mode,
        "result": result,
        "seconds": elapsed,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"Approach: multiprocessing")
        print(f"N: {args.n}")
        print(f"Workers: {args.workers}")
        print(f"Mode: {args.mode}")
        print(f"Result: {result}")
        print(f"Time: {elapsed:.6f} sec")


if __name__ == "__main__":
    main()
