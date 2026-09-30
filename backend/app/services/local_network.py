"""Local IP and default gateway detection (Windows, Linux, macOS)."""

from __future__ import annotations

import re
import socket
import struct
from pathlib import Path

from app.services.platform_utils import current_os
from app.services.runner import run_command
from app.validators import is_valid_ip

# ---------- Local IP ----------


def get_local_ip() -> str | None:
    """Find the IPv4 address used for outgoing traffic.

    Connecting a UDP socket sends no packets; it only makes the OS pick
    the outgoing interface, whose address we then read.
    """
    for probe in ("8.8.8.8", "10.255.255.255"):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(1.0)
            sock.connect((probe, 80))
            ip = sock.getsockname()[0]
            if ip and not ip.startswith("127.") and ip != "0.0.0.0":
                return ip
        except OSError:
            continue
        finally:
            sock.close()

    try:
        ip = socket.gethostbyname(socket.gethostname())
        if not ip.startswith("127."):
            return ip
    except OSError:
        pass
    return None


# ---------- Gateway parsers (pure functions, unit-tested) ----------

_WIN_ROUTE_RE = re.compile(
    r"^\s*0\.0\.0\.0\s+0\.0\.0\.0\s+(\S+)\s+(\S+)\s+(\d+)\s*$", re.MULTILINE
)
_IP_ROUTE_RE = re.compile(r"^default\s+via\s+(\S+)", re.MULTILINE)
_MAC_ROUTE_RE = re.compile(r"^\s*gateway:\s*(\S+)", re.MULTILINE)


def parse_windows_route_print(text: str) -> str | None:
    """`route print -4 0.0.0.0` -> gateway with the lowest metric."""
    best: tuple[int, str] | None = None
    for gateway, _iface, metric in _WIN_ROUTE_RE.findall(text):
        if not is_valid_ip(gateway):  # skips "On-link"
            continue
        if best is None or int(metric) < best[0]:
            best = (int(metric), gateway)
    return best[1] if best else None


def parse_proc_net_route(text: str) -> str | None:
    """/proc/net/route -> gateway of the default route with the lowest metric."""
    best: tuple[int, str] | None = None
    for line in text.splitlines()[1:]:
        cols = line.split()
        if len(cols) < 7 or cols[1] != "00000000":
            continue
        try:
            flags, metric = int(cols[3], 16), int(cols[6])
            if not flags & 0x2:  # RTF_GATEWAY
                continue
            gateway = socket.inet_ntoa(struct.pack("<L", int(cols[2], 16)))
        except (ValueError, struct.error):
            continue
        if best is None or metric < best[0]:
            best = (metric, gateway)
    return best[1] if best else None


def parse_ip_route(text: str) -> str | None:
    """`ip route show default` output."""
    for candidate in _IP_ROUTE_RE.findall(text):
        if is_valid_ip(candidate):
            return candidate
    return None


def parse_macos_route(text: str) -> str | None:
    """`route -n get default` output."""
    for candidate in _MAC_ROUTE_RE.findall(text):
        if is_valid_ip(candidate):
            return candidate
    return None


# ---------- Gateway detection ----------


def _run(args: list[str]) -> str:
    try:
        return run_command(args, timeout=5).output
    except (FileNotFoundError, OSError):
        return ""


def get_default_gateway() -> str | None:
    os_name = current_os()
    if os_name == "windows":
        return parse_windows_route_print(_run(["route", "print", "-4", "0.0.0.0"]))
    if os_name == "macos":
        return parse_macos_route(_run(["route", "-n", "get", "default"]))

    # Linux: /proc is fastest and needs no external tools.
    try:
        gateway = parse_proc_net_route(Path("/proc/net/route").read_text())
        if gateway:
            return gateway
    except OSError:
        pass
    return parse_ip_route(_run(["ip", "route", "show", "default"]))
