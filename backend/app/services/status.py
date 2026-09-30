"""Aggregates the dashboard data. Each part fails independently."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

from app.schemas import InternetStatus, StatusResult
from app.services import connectivity, dns_lookup, local_network, ping, public_ip

T = TypeVar("T")
PING_TARGET = "1.1.1.1"


def _safe(fn: Callable[[], T]) -> T | None:
    try:
        return fn()
    except Exception:  # noqa: BLE001 - a failing part must never break the dashboard
        return None


def get_status() -> StatusResult:
    with ThreadPoolExecutor(max_workers=6) as pool:
        f_internet = pool.submit(_safe, connectivity.check_internet)
        f_ping = pool.submit(_safe, lambda: ping.ping_host(PING_TARGET, count=3))
        f_local = pool.submit(_safe, local_network.get_local_ip)
        f_gateway = pool.submit(_safe, local_network.get_default_gateway)
        f_public = pool.submit(_safe, public_ip.get_public_ip)
        f_dns = pool.submit(_safe, dns_lookup.get_system_dns_server)

        internet = f_internet.result() or InternetStatus(
            online=False, message="The connection test could not be completed."
        )
        ping_result = f_ping.result()

        # Prefer ICMP numbers; fall back to the TCP connect time.
        if internet.online and ping_result and ping_result.status == "reachable":
            internet = internet.model_copy(
                update={
                    "latency_ms": ping_result.latency_ms or internet.latency_ms,
                    "packet_loss_percent": ping_result.packet_loss_percent,
                }
            )

        return StatusResult(
            internet=internet,
            local_ip=f_local.result(),
            public_ip=f_public.result(),
            gateway=f_gateway.result(),
            dns_server=f_dns.result(),
        )
