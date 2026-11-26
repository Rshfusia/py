"""Pure worker calculations for Lab 3."""

from __future__ import annotations


def process_numbers(numbers: list[int]) -> dict[str, int]:
    """Return basic statistics for a list of integers."""
    if not numbers:
        return {"count": 0, "sum": 0, "min": 0, "max": 0}
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
    }


def sum_of_squares(start: int, end: int) -> int:
    """Compute the sum of squares over inclusive range [start, end]."""
    if start > end:
        raise ValueError(f"start ({start}) must be <= end ({end}).")
    return sum(x * x for x in range(start, end + 1))
