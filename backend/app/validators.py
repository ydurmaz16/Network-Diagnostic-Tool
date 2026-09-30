"""Input validation for hostnames, IP addresses and ports.

Every value that reaches a subprocess or socket call must pass through
these helpers first. Commands are additionally executed without a shell
(see services/runner.py), so validation is defense in depth.
"""

from __future__ import annotations

import ipaddress
import re

MIN_PORT = 1
MAX_PORT = 65535

_LABEL_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$")


def is_valid_ip(value: str) -> bool:
    if not value or "%" in value:  # reject IPv6 zone ids
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def is_valid_hostname(value: str) -> bool:
    if not value or len(value) > 253:
        return False
    if value.endswith("."):
        value = value[:-1]
    labels = value.split(".")
    if not all(_LABEL_RE.match(label) for label in labels):
        return False
    # "999.1.1.1" or "1.2.3" look like malformed IPs, not hostnames.
    if labels[-1].isdigit():
        return False
    return True


def is_valid_port(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and MIN_PORT <= value <= MAX_PORT


def _to_ascii(value: str) -> str:
    """Convert internationalised domain names (e.g. türkiye.gov.tr) to punycode."""
    if value.isascii():
        return value
    try:
        return value.encode("idna").decode("ascii")
    except UnicodeError:
        return value


def validate_target(value: str) -> str:
    """Return a normalised hostname or IP address, or raise ValueError."""
    value = (value or "").strip()
    if not value:
        raise ValueError("Please enter a hostname or IP address.")
    value = _to_ascii(value)
    if is_valid_ip(value):
        return str(ipaddress.ip_address(value))
    if is_valid_hostname(value):
        return value.lower()
    raise ValueError("Invalid hostname or IP address.")


def validate_hostname(value: str) -> str:
    """Like validate_target, but IP addresses are not accepted."""
    value = validate_target(value)
    if is_valid_ip(value):
        raise ValueError("Enter a hostname (for example google.com), not an IP address.")
    return value
