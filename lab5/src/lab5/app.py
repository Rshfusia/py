"""Async workflow orchestration and CLI entry point for Lab 5."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from lab5.domain import PipelineReport, TaskItem, TaskResult, analyze_text, build_report
from lab5.storage import AsyncTaskStorage

AsyncHandler = Callable[[TaskItem], Awaitable[tuple[str, int]]]


async def default_handler(item: TaskItem) -> tuple[str, int]:
    """Simulate async I/O and run text analysis off the event loop."""
    await asyncio.sleep(0.02)
    return await asyncio.to_thread(analyze_text, item.text)


async def run_pipeline(
    items: list[TaskItem],
    storage: AsyncTaskStorage,
    *,
    max_concurrency: int = 3,
    handler: AsyncHandler = default_handler,
) -> PipelineReport:
    """Process tasks concurrently using TaskGroup and Semaphore."""
    if max_concurrency < 1:
        raise ValueError("max_concurrency must be >= 1.")

    await storage.init()
    if not items:
        return build_report([])

    semaphore = asyncio.Semaphore(max_concurrency)
    results: list[TaskResult | None] = [None] * len(items)

    async def process_one(index: int, item: TaskItem) -> None:
        async with semaphore:
            try:
                digest, words = await handler(item)
                res = TaskResult(
                    task_id=item.task_id,
                    status="success",
                    digest=digest,
                    word_count=words,
                )
            except asyncio.CancelledError:
                raise
            except (ValueError, RuntimeError, TimeoutError, OSError) as exc:
                res = TaskResult(
                    task_id=item.task_id,
                    status="failed",
                    digest=None,
                    word_count=0,
                    error=str(exc),
                )
            await storage.save(res)
            results[index] = res

    async with asyncio.TaskGroup() as tg:
        for idx, item in enumerate(items):
            tg.create_task(process_one(idx, item))

    return build_report([r for r in results if r is not None])


async def _run_demo() -> None:
    items = [
        TaskItem("t1", "async python"),
        TaskItem("t2", "task group"),
        TaskItem("t3", "semaphore limit"),
    ]
    storage = AsyncTaskStorage(":memory:")
    try:
        report = await run_pipeline(items, storage, max_concurrency=2)
        print(f"Status: {report.status}, count={len(report.results)}")
    finally:
        await storage.close()


def main() -> None:
    asyncio.run(_run_demo())


if __name__ == "__main__":
    main()
