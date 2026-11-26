"""IPC via SharedMemory + Event and multiprocessing.Queue for Lab 3."""

from __future__ import annotations

import json
import multiprocessing
import struct
from multiprocessing import shared_memory
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Event

from lab3.worker import process_numbers, sum_of_squares

HEADER_SIZE = 4


def _write_shm(shm: shared_memory.SharedMemory, data: bytes) -> None:
    if shm.buf is None:
        raise RuntimeError("Shared memory is closed.")
    total = HEADER_SIZE + len(data)
    if total > shm.size:
        raise ValueError(f"Payload ({total} bytes) exceeds buffer size ({shm.size} bytes).")
    shm.buf[:HEADER_SIZE] = struct.pack("!I", len(data))
    shm.buf[HEADER_SIZE:total] = data


def _read_shm(shm: shared_memory.SharedMemory) -> bytes:
    if shm.buf is None:
        raise RuntimeError("Shared memory is closed.")
    (length,) = struct.unpack("!I", bytes(shm.buf[:HEADER_SIZE]))
    end = HEADER_SIZE + length
    if end > shm.size:
        raise ValueError(f"Invalid length {length} for buffer size {shm.size}.")
    return bytes(shm.buf[HEADER_SIZE:end])


def _shm_child(shm_name: str, data_ready: Event, result_ready: Event) -> None:
    shm = shared_memory.SharedMemory(name=shm_name)
    try:
        if not data_ready.wait(timeout=5.0):
            raise TimeoutError("Timed out waiting for parent data.")
        numbers = json.loads(_read_shm(shm).decode("utf-8"))
        stats = process_numbers(numbers)
        _write_shm(shm, json.dumps(stats).encode("utf-8"))
        result_ready.set()
    finally:
        shm.close()


def exchange_via_shared_memory(
    numbers: list[int],
    buffer_size: int = 4096,
) -> tuple[dict[str, int], int, str]:
    """Send numbers to a child process via SharedMemory and return (stats, exitcode, shm_name)."""
    ctx = multiprocessing.get_context("spawn")
    data_ready = ctx.Event()
    result_ready = ctx.Event()
    shm = shared_memory.SharedMemory(create=True, size=buffer_size)
    proc: multiprocessing.process.BaseProcess | None = None

    try:
        payload = json.dumps(numbers).encode("utf-8")
        _write_shm(shm, payload)

        proc = ctx.Process(target=_shm_child, args=(shm.name, data_ready, result_ready))
        proc.start()
        data_ready.set()

        if not result_ready.wait(timeout=5.0):
            raise TimeoutError("Child process did not respond in time.")

        result: dict[str, int] = json.loads(_read_shm(shm).decode("utf-8"))
        proc.join(timeout=5.0)
        if proc.exitcode != 0:
            raise RuntimeError(f"Child exited with code {proc.exitcode}.")
        return result, proc.exitcode, shm.name
    finally:
        if proc is not None and proc.is_alive():
            proc.terminate()
            proc.join(timeout=1.0)
        shm.close()
        shm.unlink()


def _queue_child(
    tasks: Queue[tuple[int, int] | None],
    results: Queue[int],
) -> None:
    while True:
        item = tasks.get()
        if item is None:
            break
        start, end = item
        results.put(sum_of_squares(start, end))


def run_queue_workers(ranges: list[tuple[int, int]], workers_count: int = 2) -> list[int]:
    """Compute sum_of_squares for each range using multiple worker processes."""
    if workers_count < 1:
        raise ValueError("workers_count must be >= 1.")
    if not ranges:
        return []

    ctx = multiprocessing.get_context("spawn")
    tasks: Queue[tuple[int, int] | None] = ctx.Queue()
    results: Queue[int] = ctx.Queue()

    actual_workers = min(workers_count, len(ranges))
    procs = [
        ctx.Process(target=_queue_child, args=(tasks, results))
        for _ in range(actual_workers)
    ]

    try:
        for proc in procs:
            proc.start()
        for r in ranges:
            tasks.put(r)
        for _ in range(actual_workers):
            tasks.put(None)

        output = [results.get(timeout=5.0) for _ in ranges]
        for proc in procs:
            proc.join(timeout=5.0)
            if proc.exitcode != 0:
                raise RuntimeError(f"Worker exited with code {proc.exitcode}.")
        return output
    finally:
        for proc in procs:
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1.0)
        tasks.close()
        results.close()
