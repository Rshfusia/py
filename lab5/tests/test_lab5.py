"""Tests for Lab 5."""

from __future__ import annotations

import asyncio

import pytest

from lab5.app import run_pipeline
from lab5.domain import TaskItem, analyze_text
from lab5.storage import AsyncTaskStorage


def test_domain_analyze_text() -> None:
    digest, words = analyze_text("hello async world")
    assert len(digest) == 64
    assert words == 3


@pytest.mark.asyncio
async def test_async_workflow() -> None:
    items = [TaskItem("1", "one two"), TaskItem("2", "three")]
    storage = AsyncTaskStorage(":memory:")
    try:
        report = await run_pipeline(items, storage, max_concurrency=2)
        assert report.status == "success"
        saved = await storage.list_all()
        assert len(saved) == 2
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_semaphore_limits_concurrency() -> None:
    active = 0
    peak = 0

    async def tracked_handler(item: TaskItem) -> tuple[str, int]:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        try:
            await asyncio.sleep(0.02)
            return analyze_text(item.text)
        finally:
            active -= 1

    items = [TaskItem(f"t{i}", f"text {i}") for i in range(6)]
    storage = AsyncTaskStorage(":memory:")
    try:
        report = await run_pipeline(items, storage, max_concurrency=2, handler=tracked_handler)
        assert report.status == "success"
        assert peak == 2
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_cancellation_and_error_isolation() -> None:
    async def flaky_handler(item: TaskItem) -> tuple[str, int]:
        if item.task_id == "bad":
            raise ValueError("bad input")
        return analyze_text(item.text)

    storage = AsyncTaskStorage(":memory:")
    try:
        report = await run_pipeline(
            [TaskItem("ok", "fine"), TaskItem("bad", "x")],
            storage,
            handler=flaky_handler,
        )
        assert report.status == "partial"
    finally:
        await storage.close()

    async def slow_handler(item: TaskItem) -> tuple[str, int]:
        await asyncio.sleep(5.0)
        return analyze_text(item.text)

    storage2 = AsyncTaskStorage(":memory:")
    try:
        task = asyncio.create_task(
            run_pipeline([TaskItem("slow", "x")], storage2, handler=slow_handler)
        )
        await asyncio.sleep(0.02)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    finally:
        await storage2.close()
