"""ICMP ping through the system ping command (Windows, Linux, macOS)."""

from __future__ import annotations

import re
import socket
from dataclasses import dataclass

from app.errors import DiagnosticError
from app.schemas import PingResult
from app.services.platform_utils import current_os
from app.services.runner import run_command
from app.validators import is_valid_ip

PING_COUNT = 4
REPLY_TIMEOUT_SECONDS = 2

# A reply line contains "ttl=" in every language; the time follows "=" or "<".
# Examples: "time=24.1 ms", "time<1ms", "süre=24ms" (Turkish Windows).
_TTL_RE = re.compile(r"ttl\s*=", re.IGNORECASE)
_TIME_RE = re.compile(r"([=<])\s*(\d+(?:[.,]\d+)?)\s*ms", re.IGNORECASE)
_PERMISSION_RE = re.compile(r"operation not permitted|permission denied", re.IGNORECASE)


@dataclass(frozen=True)
class PingStats:
    received: int
    latencies: list[float]


def build_ping_command(target: str, os_name: str, count: int = PING_COUNT) -> list[str]:
    """Build the argument list. `target` must already be validated."""
    if os_name == "windows":
        return ["ping", "-n", str(count), "-w", str(REPLY_TIMEOUT_SECONDS * 1000), target]
    if os_name == "macos":  # -W is milliseconds on macOS
        return ["ping", "-c", str(count), "-W", str(REPLY_TIMEOUT_SECONDS * 1000), target]
    return ["ping", "-c", str(count), "-W", str(REPLY_TIMEOUT_SECONDS), target]


def parse_ping_output(output: str) -> PingStats:
    """Extract reply count and latencies from Windows/Linux/macOS ping output."""
    received = 0
    latencies: list[float] = []
    for line in output.splitlines():
        if not _TTL_RE.search(line):
            continue
        received += 1
        match = _TIME_RE.search(line)
        if match:
            value = float(match.group(2).replace(",", "."))
            latencies.append(1.0 if match.group(1) == "<" else value)
    return PingStats(received=received, latencies=latencies)


def ping_host(target: str, count: int = PING_COUNT) -> PingResult:
    if not is_valid_ip(target):
        try:
            socket.getaddrinfo(target, None)
        except socket.gaierror:
            return PingResult(
                host=target,
                status="unreachable",
                packets_sent=0,
                message="Hostname could not be resolved.",
            )

    command = build_ping_command(target, current_os(), count)
    timeout = count * (REPLY_TIMEOUT_SECONDS + 1) + 5
    try:
        result = run_command(command, timeout=timeout)
    except FileNotFoundError:
        raise DiagnosticError("The ping command is not available on this system.", 503)
    except OSError:
        raise DiagnosticError("Ping could not be started on this system.", 500)

    if _PERMISSION_RE.search(result.output):
        raise DiagnosticError("Ping is not permitted for the current user.", 503)

    stats = parse_ping_output(result.output)
    received = min(stats.received, count)
    loss = round((count - received) / count * 100, 1)

    if received == 0:
        return PingResult(
            host=target,
            status="unreachable",
            packet_loss_percent=100.0,
            packets_sent=count,
            packets_received=0,
            message="Host could not be reached.",
        )

    latency = round(sum(stats.latencies) / len(stats.latencies), 1) if stats.latencies else None
    return PingResult(
        host=target,
        status="reachable",
        latency_ms=latency,
        packet_loss_percent=loss,
        packets_sent=count,
        packets_received=received,
    )
