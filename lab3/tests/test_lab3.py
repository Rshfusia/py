"""Tests for Lab 3."""

from __future__ import annotations

from multiprocessing import shared_memory

import pytest

from lab3.ipc import exchange_via_shared_memory, run_queue_workers
from lab3.worker import process_numbers, sum_of_squares


def test_worker_functions() -> None:
    assert process_numbers([1, 5, 3]) == {"count": 3, "sum": 9, "min": 1, "max": 5}
    assert process_numbers([]) == {"count": 0, "sum": 0, "min": 0, "max": 0}
    assert sum_of_squares(1, 3) == 14
    with pytest.raises(ValueError):
        sum_of_squares(5, 1)


@pytest.mark.parametrize(
    "numbers",
    [
        [],
        [10, 20, 30],
        list(range(1, 300)),
    ],
)
def test_shared_memory_exchange_and_cleanup(numbers: list[int]) -> None:
    stats, exitcode, shm_name = exchange_via_shared_memory(numbers, buffer_size=4096)
    assert exitcode == 0
    assert stats == process_numbers(numbers)

    with pytest.raises(FileNotFoundError):
        shm = shared_memory.SharedMemory(name=shm_name)
        shm.close()


def test_shared_memory_overflow() -> None:
    with pytest.raises(ValueError, match="exceeds buffer size"):
        exchange_via_shared_memory(list(range(100)), buffer_size=32)


def test_queue_workers() -> None:
    partials = run_queue_workers([(1, 5), (6, 10), (11, 15)], workers_count=2)
    assert sum(partials) == sum_of_squares(1, 15)
    assert run_queue_workers([], workers_count=2) == []
