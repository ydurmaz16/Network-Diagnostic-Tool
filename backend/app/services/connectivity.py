"""Internet connectivity check using TCP connections to reliable targets."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.schemas import InternetStatus
from app.services.port_check import tcp_check

# Well-known public DNS resolvers listening on HTTPS (TCP 443).
TARGETS = (("1.1.1.1", 443), ("8.8.8.8", 443), ("9.9.9.9", 443))
TIMEOUT_SECONDS = 2.5


def check_internet() -> InternetStatus:
    with ThreadPoolExecutor(max_workers=len(TARGETS)) as pool:
        results = list(
            pool.map(lambda t: tcp_check(t[0], t[1], timeout=TIMEOUT_SECONDS), TARGETS)
        )

    times = [r.response_time_ms for r in results if r.status == "open" and r.response_time_ms is not None]
    if not times:
        return InternetStatus(
            online=False,
            message="No internet connection. None of the test servers could be reached.",
        )
    return InternetStatus(online=True, latency_ms=round(min(times), 1))
