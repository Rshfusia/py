"""TCP client for Lab 4."""

from __future__ import annotations

import argparse
import json
import socket
from types import TracebackType
from typing import Any

from lab4.protocol import FrameDecoder, encode_message


class TcpClient:
    """Framed JSON TCP client with timeout and context-manager support."""

    def __init__(self, host: str, port: int, timeout: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._sock: socket.socket | None = None
        self._decoder = FrameDecoder()
        self._queue: list[dict[str, Any]] = []

    def __enter__(self) -> TcpClient:
        self._sock = socket.create_connection((self._host, self._port), timeout=self._timeout)
        self._sock.settimeout(self._timeout)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def send_raw(self, data: bytes) -> None:
        if self._sock is None:
            raise RuntimeError("Client is not connected.")
        self._sock.sendall(data)

    def receive_one(self) -> dict[str, Any]:
        if self._sock is None:
            raise RuntimeError("Client is not connected.")
        if self._queue:
            return self._queue.pop(0)
        while True:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("Server closed connection.")
            frames = self._decoder.feed(chunk)
            if frames:
                self._queue.extend(frames[1:])
                return frames[0]

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send one request dict and wait for its decoded response."""
        self.send_raw(encode_message(payload))
        return self.receive_one()


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab 4 TCP Client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--action", default="ping")
    parser.add_argument("--message", default=None)
    args = parser.parse_args()

    payload: dict[str, Any] = {"action": args.action}
    if args.message is not None:
        payload["message"] = args.message

    with TcpClient(args.host, args.port) as client:
        print(json.dumps(client.request(payload), ensure_ascii=False))


if __name__ == "__main__":
    main()
