import socket
from contextlib import contextmanager

from app.services import port_check


@contextmanager
def _ok():
    yield object()


def _patch(monkeypatch, behaviour):
    def fake(*args, **kwargs):
        if isinstance(behaviour, Exception):
            raise behaviour
        return behaviour()

    monkeypatch.setattr(port_check.socket, "create_connection", fake)


def test_open(monkeypatch):
    _patch(monkeypatch, _ok)
    result = port_check.tcp_check("192.168.1.1", 80)
    assert result.status == "open" and result.response_time_ms is not None


def test_closed(monkeypatch):
    _patch(monkeypatch, ConnectionRefusedError())
    assert port_check.tcp_check("192.168.1.1", 81).status == "closed"


def test_timeout(monkeypatch):
    _patch(monkeypatch, TimeoutError())
    assert port_check.tcp_check("192.168.1.1", 81).status == "timeout"


def test_dns_failure(monkeypatch):
    _patch(monkeypatch, socket.gaierror())
    result = port_check.tcp_check("nope.invalid", 80)
    assert result.status == "error" and "resolved" in result.message


def test_network_unreachable(monkeypatch):
    _patch(monkeypatch, OSError("Network is unreachable"))
    result = port_check.tcp_check("10.0.0.1", 80)
    assert result.status == "error"
    assert "unreachable" not in result.message.lower() or "could not be reached" in result.message
