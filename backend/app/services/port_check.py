"""Single host + single port TCP connection check. Not a port scanner."""

from __future__ import annotations

import socket
import time

from app.schemas import PortCheckResult

CONNECT_TIMEOUT = 3.0


def tcp_check(host: str, port: int, timeout: float = CONNECT_TIMEOUT) -> PortCheckResult:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = (time.perf_counter() - start) * 1000
        return PortCheckResult(
            host=host, port=port, status="open", response_time_ms=round(elapsed, 1)
        )
    except socket.gaierror:
        return PortCheckResult(
            host=host, port=port, status="error", message="Hostname could not be resolved."
        )
    except ConnectionRefusedError:
        return PortCheckResult(
            host=host, port=port, status="closed", message="The host refused the connection."
        )
    except TimeoutError:
        return PortCheckResult(
            host=host,
            port=port,
            status="timeout",
            message="The connection timed out. The port may be filtered or the host is down.",
        )
    except OSError:
        return PortCheckResult(
            host=host,
            port=port,
            status="error",
            message="The host could not be reached from this network.",
        )
