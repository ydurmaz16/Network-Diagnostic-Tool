"""HTTP endpoints. Blocking network work runs in a thread pool."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter

from app.schemas import (
    DnsRequest,
    DnsResult,
    GatewayResult,
    LocalIpResult,
    PingResult,
    PortCheckRequest,
    PortCheckResult,
    PublicIpResult,
    StatusResult,
    TargetRequest,
    TracerouteResult,
)
from app.services import dns_lookup, local_network, ping, port_check, public_ip, status, traceroute

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("/status", response_model=StatusResult)
async def get_status() -> StatusResult:
    return await asyncio.to_thread(status.get_status)


@router.get("/local-ip", response_model=LocalIpResult)
async def get_local_ip() -> LocalIpResult:
    ip = await asyncio.to_thread(local_network.get_local_ip)
    if ip is None:
        return LocalIpResult(message="Local IP address could not be detected.")
    return LocalIpResult(local_ip=ip)


@router.get("/public-ip", response_model=PublicIpResult)
async def get_public_ip() -> PublicIpResult:
    ip = await asyncio.to_thread(public_ip.get_public_ip)
    if ip is None:
        return PublicIpResult(message="Public IP could not be retrieved. Check your connection.")
    return PublicIpResult(public_ip=ip)


@router.get("/gateway", response_model=GatewayResult)
async def get_gateway() -> GatewayResult:
    gateway = await asyncio.to_thread(local_network.get_default_gateway)
    if gateway is None:
        return GatewayResult(message="Gateway could not be detected")
    return GatewayResult(gateway=gateway)


@router.post("/ping", response_model=PingResult)
async def run_ping(request: TargetRequest) -> PingResult:
    return await asyncio.to_thread(ping.ping_host, request.target)


@router.post("/dns", response_model=DnsResult)
async def run_dns(request: DnsRequest) -> DnsResult:
    return await asyncio.to_thread(dns_lookup.lookup, request.hostname)


@router.post("/traceroute", response_model=TracerouteResult)
async def run_traceroute(request: TargetRequest) -> TracerouteResult:
    return await asyncio.to_thread(traceroute.run_traceroute, request.target)


@router.post("/port-check", response_model=PortCheckResult)
async def run_port_check(request: PortCheckRequest) -> PortCheckResult:
    return await asyncio.to_thread(port_check.tcp_check, request.host, request.port)
