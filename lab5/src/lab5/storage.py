"""Non-blocking SQLite storage layer for Lab 5."""

from __future__ import annotations

import asyncio
import sqlite3

from lab5.domain import TaskResult


class AsyncTaskStorage:
    """Async wrapper around sqlite3 using asyncio.to_thread to avoid blocking the event loop."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()

    async def init(self) -> None:
        async with self._lock:
            if self._conn is None:
                self._conn = await asyncio.to_thread(self._connect_sync)

    async def save(self, result: TaskResult) -> None:
        async with self._lock:
            if self._conn is None:
                raise RuntimeError("Storage is not initialized.")
            await asyncio.to_thread(self._save_sync, self._conn, result)

    async def list_all(self) -> list[TaskResult]:
        async with self._lock:
            if self._conn is None:
                raise RuntimeError("Storage is not initialized.")
            return await asyncio.to_thread(self._list_sync, self._conn)

    async def close(self) -> None:
        async with self._lock:
            if self._conn is not None:
                conn = self._conn
                self._conn = None
                await asyncio.to_thread(conn.close)

    def _connect_sync(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_results (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                digest TEXT,
                word_count INTEGER NOT NULL,
                error TEXT
            )
            """
        )
        conn.commit()
        return conn

    @staticmethod
    def _save_sync(conn: sqlite3.Connection, result: TaskResult) -> None:
        conn.execute(
            """
            INSERT OR REPLACE INTO task_results (task_id, status, digest, word_count, error)
            VALUES (?, ?, ?, ?, ?)
            """,
            (result.task_id, result.status, result.digest, result.word_count, result.error),
        )
        conn.commit()

    @staticmethod
    def _list_sync(conn: sqlite3.Connection) -> list[TaskResult]:
        rows = conn.execute(
            "SELECT task_id, status, digest, word_count, error FROM task_results ORDER BY task_id"
        ).fetchall()
        return [
            TaskResult(
                task_id=str(row[0]),
                status=str(row[1]),
                digest=str(row[2]) if row[2] is not None else None,
                word_count=int(row[3]),
                error=str(row[4]) if row[4] is not None else None,
            )
            for row in rows
        ]
