"""Entry point for Lab 3 demonstration."""

from __future__ import annotations

from lab3.ipc import exchange_via_shared_memory, run_queue_workers


def main() -> None:
    """Run SharedMemory and Queue IPC demonstrations."""
    stats, exitcode, _ = exchange_via_shared_memory([3, 7, 10, 20])
    print(f"SharedMemory result: {stats}, child exitcode={exitcode}")

    partials = run_queue_workers([(1, 50), (51, 100)], workers_count=2)
    print(f"Queue workers sum_of_squares(1..100) = {sum(partials)}")


if __name__ == "__main__":
    main()
