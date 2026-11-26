"""Length-prefixed JSON framing protocol over TCP."""

from __future__ import annotations

import json
import struct
from typing import Any

HEADER_SIZE = 4
MAX_MESSAGE_SIZE = 1024 * 1024  # 1 MiB


class ProtocolError(ValueError):
    """Raised on invalid frame header or malformed JSON payload."""


def encode_message(payload: dict[str, Any]) -> bytes:
    """Pack a dict as [4-byte Big-Endian length][UTF-8 JSON]."""
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(body) == 0 or len(body) > MAX_MESSAGE_SIZE:
        raise ProtocolError(f"Message size {len(body)} out of range.")
    return struct.pack("!I", len(body)) + body


class FrameDecoder:
    """Incremental decoder handling fragmented and coalesced TCP chunks."""

    def __init__(self, max_size: int = MAX_MESSAGE_SIZE) -> None:
        self._max_size = max_size
        self._buffer = bytearray()

    def feed(self, chunk: bytes) -> list[dict[str, Any]]:
        """Append bytes and return all complete JSON objects decoded so far."""
        self._buffer.extend(chunk)
        messages: list[dict[str, Any]] = []

        while len(self._buffer) >= HEADER_SIZE:
            (length,) = struct.unpack("!I", self._buffer[:HEADER_SIZE])
            if length == 0 or length > self._max_size:
                self._buffer.clear()
                raise ProtocolError(f"Invalid frame length: {length}.")

            frame_end = HEADER_SIZE + length
            if len(self._buffer) < frame_end:
                break

            raw_body = bytes(self._buffer[HEADER_SIZE:frame_end])
            del self._buffer[:frame_end]

            try:
                data = json.loads(raw_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProtocolError(f"Invalid JSON payload: {exc}") from exc

            if not isinstance(data, dict):
                raise ProtocolError("JSON payload must be an object.")
            messages.append(data)

        return messages
