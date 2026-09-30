"""Public IP lookup through third-party APIs. Never raises."""

from __future__ import annotations

import httpx

from app.validators import is_valid_ip

PROVIDERS = (
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://ifconfig.me/ip",
)
TIMEOUT_SECONDS = 3.0


def get_public_ip() -> str | None:
    """Return the public IP, or None if every provider fails."""
    for url in PROVIDERS:
        try:
            response = httpx.get(url, timeout=TIMEOUT_SECONDS, follow_redirects=True)
            response.raise_for_status()
            candidate = response.text.strip()
            if is_valid_ip(candidate):
                return candidate
        except (httpx.HTTPError, ValueError):
            continue
    return None
