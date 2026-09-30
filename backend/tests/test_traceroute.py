from app.services import traceroute
from app.services.runner import CommandResult

LINUX = """traceroute to google.com (142.250.1.1), 20 hops max, 60 byte packets
 1  192.168.1.1  1.234 ms  1.100 ms
 2  10.20.0.1  8.500 ms  9.500 ms
 3  * *
 4  142.250.1.1  20.0 ms  22.0 ms
"""

WINDOWS = """Tracing route to google.com [142.250.1.1]
over a maximum of 20 hops:

  1    <1 ms    <1 ms    <1 ms  192.168.1.1
  2     8 ms     9 ms    10 ms  10.20.0.1
  3     *        *        *     Request timed out.
  4    20 ms    22 ms    21 ms  142.250.1.1

Trace complete.
"""


def test_parse_linux():
    hops = traceroute.parse_traceroute_output(LINUX)
    assert [h.hop for h in hops] == [1, 2, 3, 4]
    assert hops[0].address == "192.168.1.1" and hops[0].latency_ms == 1.2
    assert hops[2].address is None and hops[2].latency_ms is None
    assert hops[3].latency_ms == 21.0


def test_parse_windows():
    hops = traceroute.parse_traceroute_output(WINDOWS)
    assert len(hops) == 4
    assert hops[0].latency_ms == 1.0  # "<1 ms"
    assert hops[1].address == "10.20.0.1" and hops[1].latency_ms == 9.0
    assert hops[2].address is None
    assert hops[3].address == "142.250.1.1"


def test_build_command_is_list_and_target_last():
    for os_name in ("windows", "linux", "macos"):
        cmd = traceroute.build_traceroute_command("google.com", os_name)
        assert isinstance(cmd, list) and cmd[-1] == "google.com"
    assert traceroute.build_traceroute_command("x.com", "windows")[0] == "tracert"
    assert traceroute.build_traceroute_command("x.com", "linux")[0] == "traceroute"


def test_run_traceroute_completed(monkeypatch):
    monkeypatch.setattr(traceroute, "_resolve_ips", lambda t: {"142.250.1.1"})
    monkeypatch.setattr(traceroute, "run_command", lambda *a, **k: CommandResult(0, LINUX))
    result = traceroute.run_traceroute("google.com")
    assert result.status == "completed" and len(result.hops) == 4


def test_run_traceroute_incomplete(monkeypatch):
    monkeypatch.setattr(traceroute, "_resolve_ips", lambda t: {"9.9.9.9"})
    monkeypatch.setattr(traceroute, "run_command", lambda *a, **k: CommandResult(0, LINUX))
    assert traceroute.run_traceroute("x.com").status == "incomplete"


def test_run_traceroute_failed_output(monkeypatch):
    monkeypatch.setattr(traceroute, "_resolve_ips", lambda t: {"9.9.9.9"})
    monkeypatch.setattr(traceroute, "run_command", lambda *a, **k: CommandResult(1, "error"))
    assert traceroute.run_traceroute("x.com").status == "failed"


def test_run_traceroute_unresolvable(monkeypatch):
    monkeypatch.setattr(traceroute, "_resolve_ips", lambda t: set())
    result = traceroute.run_traceroute("nope.invalid")
    assert result.status == "failed" and "resolved" in result.message
