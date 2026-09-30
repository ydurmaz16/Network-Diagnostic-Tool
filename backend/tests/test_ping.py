import pytest

from app.errors import DiagnosticError
from app.services import ping
from app.services.runner import CommandResult

LINUX_OK = """PING google.com (142.250.1.1) 56(84) bytes of data.
64 bytes from 142.250.1.1: icmp_seq=1 ttl=117 time=24.1 ms
64 bytes from 142.250.1.1: icmp_seq=2 ttl=117 time=22.9 ms
64 bytes from 142.250.1.1: icmp_seq=3 ttl=117 time=25.0 ms
64 bytes from 142.250.1.1: icmp_seq=4 ttl=117 time=24.0 ms

--- google.com ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
"""

WINDOWS_EN = """Pinging google.com [142.250.1.1] with 32 bytes of data:
Reply from 142.250.1.1: bytes=32 time=24ms TTL=117
Reply from 142.250.1.1: bytes=32 time<1ms TTL=117
Request timed out.
Reply from 142.250.1.1: bytes=32 time=26ms TTL=117
"""

WINDOWS_TR = """google.com [142.250.1.1] adresine 32 bayt veriyle ping atiliyor:
142.250.1.1 adresinden yanit: bayt=32 süre=24ms TTL=117
142.250.1.1 adresinden yanit: bayt=32 süre=20ms TTL=117
Istek zaman asimina ugradi.
Istek zaman asimina ugradi.
"""

ALL_LOST = """Pinging 10.9.9.9 with 32 bytes of data:
Reply from 192.168.1.1: Destination host unreachable.
Request timed out.
"""


def test_parse_linux():
    stats = ping.parse_ping_output(LINUX_OK)
    assert stats.received == 4
    assert stats.latencies == [24.1, 22.9, 25.0, 24.0]


def test_parse_windows_english_with_sub_ms():
    stats = ping.parse_ping_output(WINDOWS_EN)
    assert stats.received == 3
    assert stats.latencies == [24.0, 1.0, 26.0]


def test_parse_windows_turkish():
    stats = ping.parse_ping_output(WINDOWS_TR)
    assert stats.received == 2
    assert stats.latencies == [24.0, 20.0]


def test_parse_no_replies():
    stats = ping.parse_ping_output(ALL_LOST)
    assert stats.received == 0 and stats.latencies == []


def test_build_command_is_argument_list_with_target_last():
    for os_name in ("windows", "linux", "macos"):
        cmd = ping.build_ping_command("google.com", os_name)
        assert isinstance(cmd, list)
        assert cmd[0] == "ping" and cmd[-1] == "google.com"


def test_ping_host_success(monkeypatch):
    monkeypatch.setattr(ping, "run_command", lambda *a, **k: CommandResult(0, LINUX_OK))
    result = ping.ping_host("8.8.8.8")
    assert result.status == "reachable"
    assert result.latency_ms == 24.0
    assert result.packet_loss_percent == 0.0


def test_ping_host_partial_loss(monkeypatch):
    monkeypatch.setattr(ping, "run_command", lambda *a, **k: CommandResult(1, WINDOWS_EN))
    result = ping.ping_host("8.8.8.8")
    assert result.status == "reachable"
    assert result.packet_loss_percent == 25.0


def test_ping_host_unreachable(monkeypatch):
    monkeypatch.setattr(ping, "run_command", lambda *a, **k: CommandResult(1, ALL_LOST))
    result = ping.ping_host("10.9.9.9")
    assert result.status == "unreachable"
    assert result.message == "Host could not be reached."


def test_ping_host_unresolvable(monkeypatch):
    import socket

    def boom(*a, **k):
        raise socket.gaierror

    monkeypatch.setattr(ping.socket, "getaddrinfo", boom)
    result = ping.ping_host("nonexistent.invalid")
    assert result.status == "unreachable"
    assert "resolved" in result.message


def test_ping_missing_command(monkeypatch):
    def missing(*a, **k):
        raise FileNotFoundError

    monkeypatch.setattr(ping, "run_command", missing)
    with pytest.raises(DiagnosticError):
        ping.ping_host("8.8.8.8")
