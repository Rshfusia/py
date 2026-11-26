"""Core domain models and pure logic for Lab 5."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskItem:
    task_id: str
    text: str


@dataclass(frozen=True, slots=True)
class TaskResult:
    task_id: str
    status: str
    digest: str | None
    word_count: int
    error: str | None = None


@dataclass(frozen=True, slots=True)
class PipelineReport:
    status: str
    results: tuple[TaskResult, ...]


def analyze_text(text: str) -> tuple[str, int]:
    """Pure computation returning (sha256_hex, word_count)."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digest, len(text.split())


def build_report(results: list[TaskResult]) -> PipelineReport:
    """Aggregate task results into a PipelineReport."""
    failed = sum(1 for item in results if item.status != "success")
    if failed == 0:
        status = "success"
    elif failed < len(results):
        status = "partial"
    else:
        status = "failed"
    return PipelineReport(status=status, results=tuple(results))
