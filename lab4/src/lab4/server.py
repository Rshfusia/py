"""Non-blocking multiplexed TCP server using selectors."""

from __future__ import annotations

import argparse
import selectors
import socket
import threading
from dataclasses import dataclass, field
from typing import Any

from lab4.protocol import FrameDecoder, ProtocolError, encode_message


def handle_command(request: dict[str, Any], store: dict[str, Any]) -> dict[str, Any]:
    """Pure request handler decoupled from sockets."""
    action = request.get("action")
    if action == "ping":
        return {"status": "ok", "pong": True}
    if action == "echo":
        return {"status": "ok", "message": request.get("message")}
    if action == "set":
        key = request.get("key")
        if not isinstance(key, str) or not key:
            return {"status": "error", "error": "Invalid key."}
        store[key] = request.get("value")
        return {"status": "ok", "key": key}
    if action == "get":
        key = request.get("key")
        if not isinstance(key, str) or key not in store:
            return {"status": "error", "error": "Key not found."}
        return {"status": "ok", "key": key, "value": store[key]}
    return {"status": "error", "error": f"Unknown action: {action!r}"}


@dataclass(slots=True)
class _ClientConn:
    sock: socket.socket
    decoder: FrameDecoder = field(default_factory=FrameDecoder)
    outbox: bytearray = field(default_factory=bytearray)
    close_after_send: bool = False


class TcpServer:
    """Non-blocking TCP server powered by selectors.DefaultSelector."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        self._host = host
        self._port = port
        self._store: dict[str, Any] = {}
        self._selector = selectors.DefaultSelector()
        self._server_sock: socket.socket | None = None
        self._clients: dict[int, _ClientConn] = {}
        self._stop_event = threading.Event()
        self._address: tuple[str, int] | None = None

    @property
    def address(self) -> tuple[str, int]:
        if self._address is None:
            raise RuntimeError("Server is not started.")
        return self._address

    def start(self) -> tuple[str, int]:
        """Bind socket, register in selector, and return (host, port)."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self._host, self._port))
        sock.listen(64)
        sock.setblocking(False)

        self._selector.register(sock, selectors.EVENT_READ, data="accept")
        self._server_sock = sock
        host, port = sock.getsockname()[:2]
        self._address = (str(host), int(port))
        return self._address

    def serve_forever(self) -> None:
        """Run the selector event loop until stop() is called."""
        if self._server_sock is None:
            self.start()

        try:
            while not self._stop_event.is_set():
                for key, mask in self._selector.select(timeout=0.05):
                    if key.data == "accept":
                        self._accept()
                    elif isinstance(key.data, _ClientConn):
                        conn = key.data
                        if mask & selectors.EVENT_READ:
                            self._on_read(conn)
                        if (mask & selectors.EVENT_WRITE) and conn.sock.fileno() in self._clients:
                            self._on_write(conn)
        finally:
            self.close()

    def stop(self) -> None:
        """Stop the server loop."""
        self._stop_event.set()

    def close(self) -> None:
        """Release all sockets and close selector."""
        for conn in list(self._clients.values()):
            self._close_client(conn)
        if self._server_sock is not None:
            try:
                self._selector.unregister(self._server_sock)
            except (KeyError, ValueError):
                pass
            self._server_sock.close()
            self._server_sock = None
        self._selector.close()

    def _accept(self) -> None:
        if self._server_sock is None:
            return
        while True:
            try:
                client_sock, _ = self._server_sock.accept()
            except BlockingIOError:
                break
            client_sock.setblocking(False)
            conn = _ClientConn(sock=client_sock)
            self._clients[client_sock.fileno()] = conn
            self._selector.register(client_sock, selectors.EVENT_READ, data=conn)

    def _on_read(self, conn: _ClientConn) -> None:
        try:
            chunk = conn.sock.recv(4096)
        except BlockingIOError:
            return
        except OSError:
            self._close_client(conn)
            return

        if not chunk:
            self._close_client(conn)
            return

        try:
            messages = conn.decoder.feed(chunk)
        except ProtocolError as exc:
            conn.outbox.extend(encode_message({"status": "error", "error": str(exc)}))
            conn.close_after_send = True
            self._set_events(conn)
            return

        for msg in messages:
            reply = handle_command(msg, self._store)
            conn.outbox.extend(encode_message(reply))
        if conn.outbox:
            self._set_events(conn)

    def _on_write(self, conn: _ClientConn) -> None:
        try:
            sent = conn.sock.send(conn.outbox)
        except BlockingIOError:
            return
        except OSError:
            self._close_client(conn)
            return

        del conn.outbox[:sent]
        if not conn.outbox and conn.close_after_send:
            self._close_client(conn)
        else:
            self._set_events(conn)

    def _set_events(self, conn: _ClientConn) -> None:
        events = selectors.EVENT_READ | (selectors.EVENT_WRITE if conn.outbox else 0)
        try:
            self._selector.modify(conn.sock, events, data=conn)
        except (KeyError, ValueError):
            self._close_client(conn)

    def _close_client(self, conn: _ClientConn) -> None:
        self._clients.pop(conn.sock.fileno(), None)
        try:
            self._selector.unregister(conn.sock)
        except (KeyError, ValueError):
            pass
        try:
            conn.sock.close()
        except OSError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab 4 TCP Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    server = TcpServer(args.host, args.port)
    host, port = server.start()
    print(f"Server listening on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
