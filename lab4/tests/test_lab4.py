"""Tests for Lab 4."""

from __future__ import annotations

import socket
import struct
import threading
from collections.abc import Iterator

import pytest

from lab4.client import TcpClient
from lab4.protocol import FrameDecoder, ProtocolError, encode_message
from lab4.server import TcpServer


@pytest.fixture()
def server_addr() -> Iterator[tuple[str, int]]:
    server = TcpServer("127.0.0.1", port=0)
    addr = server.start()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield addr
    finally:
        server.stop()
        thread.join(timeout=2.0)


def test_framing_fragmented_and_coalesced() -> None:
    raw = encode_message({"action": "ping"}) + encode_message({"action": "echo", "message": "hi"})
    decoder = FrameDecoder()
    decoded: list[dict[str, object]] = []
    for i in range(len(raw)):
        decoded.extend(decoder.feed(raw[i : i + 1]))
    assert decoded == [{"action": "ping"}, {"action": "echo", "message": "hi"}]

    with pytest.raises(ProtocolError):
        FrameDecoder(max_size=10).feed(struct.pack("!I", 100))


def test_client_server_roundtrip(server_addr: tuple[str, int]) -> None:
    host, port = server_addr
    with TcpClient(host, port) as client:
        assert client.request({"action": "ping"}) == {"status": "ok", "pong": True}
        assert client.request({"action": "set", "key": "x", "value": 123}) == {
            "status": "ok",
            "key": "x",
        }
        assert client.request({"action": "get", "key": "x"}) == {
            "status": "ok",
            "key": "x",
            "value": 123,
        }


def test_concurrent_clients_and_large_payload(server_addr: tuple[str, int]) -> None:
    host, port = server_addr
    errors: list[BaseException] = []

    def run_client(idx: int) -> None:
        try:
            with TcpClient(host, port) as client:
                msg = f"{idx}-" + ("A" * 20_000)
                resp = client.request({"action": "echo", "message": msg})
                assert resp == {"status": "ok", "message": msg}
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=run_client, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)
    assert not errors


def test_invalid_packet_and_disconnect(server_addr: tuple[str, int]) -> None:
    host, port = server_addr
    bad_body = b"{not-json"
    with TcpClient(host, port) as client:
        client.send_raw(struct.pack("!I", len(bad_body)) + bad_body)
        resp = client.receive_one()
        assert resp["status"] == "error"

    with socket.create_connection((host, port), timeout=2.0) as raw:
        raw.sendall(struct.pack("!I", 50) + b"cut")

    with TcpClient(host, port) as client:
        assert client.request({"action": "ping"}) == {"status": "ok", "pong": True}
