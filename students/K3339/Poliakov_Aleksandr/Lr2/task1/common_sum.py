from __future__ import annotations

from dataclasses import dataclass

DEFAULT_N = 10_000_000_000_000


@dataclass(frozen=True)
class RangePart:
    start: int
    end: int


def split_range(start: int, end: int, parts: int) -> list[RangePart]:
    if parts <= 0:
        raise ValueError("parts must be positive")
    if start > end:
        raise ValueError("start must be <= end")

    total_numbers = end - start + 1
    base_size, remainder = divmod(total_numbers, parts)
    ranges: list[RangePart] = []
    current = start

    for index in range(parts):
        size = base_size + (1 if index < remainder else 0)
        if size <= 0:
            break
        range_end = current + size - 1
        ranges.append(RangePart(current, range_end))
        current = range_end + 1

    return ranges


def arithmetic_sum(start: int, end: int) -> int:
    count = end - start + 1
    return (start + end) * count // 2


def loop_sum(start: int, end: int) -> int:
    total = 0
    for value in range(start, end + 1):
        total += value
    return total


def calculate_range_sum(start: int, end: int, mode: str) -> int:
    if mode == "formula":
        return arithmetic_sum(start, end)
    if mode == "loop":
        return loop_sum(start, end)
    raise ValueError("mode must be 'formula' or 'loop'")
