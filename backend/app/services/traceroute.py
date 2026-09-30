"""Traceroute through tracert (Windows) or traceroute (Linux/macOS)."""

from __future__ import annotations

import ipaddress
import re
import socket

from app.errors import DiagnosticError
from app.schemas import TracerouteHop, TracerouteResult
from app.services.platform_utils import current_os
from app.services.runner import run_command
from app.validators import is_valid_ip

MAX_HOPS = 20
COMMAND_TIMEOUT = 75

_HOP_LINE_RE = re.compile(r"^\s*(\d{1,2})\s+(.*)$")
_LATENCY_RE = re.compile(r"(<)?\s*(\d+(?:[.,]\d+)?)\s*ms", re.IGNORECASE)
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def build_traceroute_command(target: str, os_name: str) -> list[str]:
    """Build the argument list. `target` must already be validated."""
    if os_name == "windows":
        return ["tracert", "-d", "-h", str(MAX_HOPS), "-w", "1000", target]
    return ["traceroute", "-n", "-m", str(MAX_HOPS), "-q", "2", "-w", "1", target]


def parse_traceroute_output(output: str) -> list[TracerouteHop]:
    """Parse tracert / traceroute output into hops (locale independent)."""
    hops: list[TracerouteHop] = []
    for line in output.splitlines():
        match = _HOP_LINE_RE.match(line)
        if not match:
            continue
        number = int(match.group(1))
        rest = match.group(2)

        address = None
        for candidate in _IPV4_RE.findall(rest):
            try:
                address = str(ipaddress.IPv4Address(candidate))
                break
            except ValueError:
                continue

        values: list[float] = []
        for lt, number_text in _LATENCY_RE.findall(rest):
            values.append(1.0 if lt else float(number_text.replace(",", ".")))
        latency = round(sum(values) / len(values), 1) if values else None

        hops.append(TracerouteHop(hop=number, address=address, latency_ms=latency))
    return hops


def _resolve_ips(target: str) -> set[str]:
    if is_valid_ip(target):
        return {str(ipaddress.ip_address(target))}
    try:
        return {str(info[4][0]) for info in socket.getaddrinfo(target, None)}
    except socket.gaierror:
        return set()


def run_traceroute(target: str) -> TracerouteResult:
    destination_ips = _resolve_ips(target)
    if not destination_ips:
        return TracerouteResult(
            target=target, status="failed", message="Hostname could not be resolved."
        )

    command = build_traceroute_command(target, current_os())
    try:
        result = run_command(command, timeout=COMMAND_TIMEOUT)
    except FileNotFoundError:
        if current_os() == "windows":
            raise DiagnosticError("The tracert command is not available on this system.", 503)
        raise DiagnosticError(
            "The traceroute command is not installed. "
            "On Debian/Ubuntu run: sudo apt install traceroute",
            503,
        )
    except OSError:
        raise DiagnosticError("Traceroute could not be started on this system.", 500)

    hops = parse_traceroute_output(result.output)
    if not hops:
        return TracerouteResult(
            target=target, status="failed", message="Traceroute failed. No hops were returned."
        )

    reached = hops[-1].address in destination_ips
    if reached and not result.timed_out:
        return TracerouteResult(target=target, status="completed", hops=hops)

    message = (
        "The trace took too long and was stopped. Showing the hops found so far."
        if result.timed_out
        else f"The destination was not reached within {MAX_HOPS} hops. "
        "Some routers do not answer traceroute probes."
    )
    return TracerouteResult(target=target, status="incomplete", hops=hops, message=message)
