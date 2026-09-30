"""DNS lookup using the system's configured DNS server (via dnspython)."""

from __future__ import annotations

import socket
import time
from typing import Iterable

import dns.exception
import dns.resolver

from app.schemas import DnsResult

QUERY_TIMEOUT = 2.0
QUERY_LIFETIME = 4.0


def extract_addresses(answer: Iterable) -> list[str]:
    """Return the IP addresses from a dnspython Answer or RRset (deduplicated)."""
    seen: list[str] = []
    for record in answer:
        address = getattr(record, "address", None)
        if address and address not in seen:
            seen.append(address)
    return seen


def get_system_dns_server() -> str | None:
    try:
        resolver = dns.resolver.Resolver()
    except dns.resolver.NoResolverConfiguration:
        return None
    return resolver.nameservers[0] if resolver.nameservers else None


def _fallback_lookup(hostname: str) -> DnsResult:
    """Used when no resolver configuration can be read (rare)."""
    start = time.perf_counter()
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return DnsResult(
            hostname=hostname, status="failed", message="Hostname could not be resolved."
        )
    elapsed = round((time.perf_counter() - start) * 1000, 1)
    addresses: list[str] = []
    for info in infos:
        address = str(info[4][0])
        if address not in addresses:
            addresses.append(address)
    return DnsResult(
        hostname=hostname,
        status="resolved",
        addresses=addresses,
        response_time_ms=elapsed,
    )


def lookup(hostname: str) -> DnsResult:
    try:
        resolver = dns.resolver.Resolver()
    except dns.resolver.NoResolverConfiguration:
        return _fallback_lookup(hostname)

    resolver.timeout = QUERY_TIMEOUT
    resolver.lifetime = QUERY_LIFETIME
    server = resolver.nameservers[0] if resolver.nameservers else None

    addresses: list[str] = []
    elapsed_ms: float | None = None
    start = time.perf_counter()
    try:
        answer = resolver.resolve(hostname, "A")
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        addresses += extract_addresses(answer)
    except dns.resolver.NoAnswer:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    except dns.resolver.NXDOMAIN:
        return DnsResult(
            hostname=hostname,
            status="failed",
            dns_server=server,
            message="Hostname could not be resolved.",
        )
    except dns.exception.Timeout:
        return DnsResult(
            hostname=hostname,
            status="failed",
            dns_server=server,
            message="The DNS server did not respond in time.",
        )
    except (dns.resolver.NoNameservers, dns.exception.DNSException):
        return DnsResult(
            hostname=hostname,
            status="failed",
            dns_server=server,
            message="DNS lookup failed. Check your DNS settings.",
        )

    # IPv6 addresses are a bonus; failures here are ignored.
    try:
        addresses += [a for a in extract_addresses(resolver.resolve(hostname, "AAAA")) if a not in addresses]
    except dns.exception.DNSException:
        pass

    if not addresses:
        return DnsResult(
            hostname=hostname,
            status="failed",
            dns_server=server,
            response_time_ms=elapsed_ms,
            message="No IP addresses were found for this hostname.",
        )

    return DnsResult(
        hostname=hostname,
        status="resolved",
        addresses=addresses,
        dns_server=server,
        response_time_ms=elapsed_ms,
    )
