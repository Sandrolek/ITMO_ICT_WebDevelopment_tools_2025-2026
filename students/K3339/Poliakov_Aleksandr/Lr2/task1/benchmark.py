from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    ("threading", "threading_app.py"),
    ("multiprocessing", "multiprocessing_app.py"),
    ("asyncio", "asyncio_app.py"),
]


def run_script(script: str, n: int, workers: int, mode: str) -> float:
    command = [
        sys.executable,
        script,
        "--n",
        str(n),
        "--workers",
        str(workers),
        "--mode",
        mode,
        "--json",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    return float(payload["seconds"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark task 1 implementations")
    parser.add_argument("--n", type=int, default=50_000_000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--mode", choices=("formula", "loop"), default="loop")
    parser.add_argument("--repeats", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent

    print(f"Task 1 benchmark: n={args.n}, workers={args.workers}, mode={args.mode}, repeats={args.repeats}")
    print()
    print("| Подход | Min, сек | Mean, сек | Max, сек |")
    print("|---|---:|---:|---:|")

    for approach, script in SCRIPTS:
        times = [run_script(str(root / script), args.n, args.workers, args.mode) for _ in range(args.repeats)]
        print(
            f"| {approach} | {min(times):.6f} | "
            f"{statistics.mean(times):.6f} | {max(times):.6f} |"
        )


if __name__ == "__main__":
    main()
