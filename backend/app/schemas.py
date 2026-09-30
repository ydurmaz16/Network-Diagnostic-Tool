"""Pydantic request and response models."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.validators import validate_hostname, validate_target

# ---------- Requests ----------


def _strip(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


class TargetRequest(BaseModel):
    """Hostname or IP address (ping, traceroute)."""

    target: str

    _strip_target = field_validator("target", mode="before")(_strip)

    @field_validator("target")
    @classmethod
    def _check_target(cls, value: str) -> str:
        return validate_target(value)


class DnsRequest(BaseModel):
    """Hostname only (DNS lookup)."""

    hostname: str

    _strip_hostname = field_validator("hostname", mode="before")(_strip)

    @field_validator("hostname")
    @classmethod
    def _check_hostname(cls, value: str) -> str:
        return validate_hostname(value)


class PortCheckRequest(BaseModel):
    """A single host + single port. Never a range."""

    host: str
    port: int = Field(ge=1, le=65535)

    _strip_host = field_validator("host", mode="before")(_strip)

    @field_validator("host")
    @classmethod
    def _check_host(cls, value: str) -> str:
        return validate_target(value)


# ---------- Responses ----------


class InternetStatus(BaseModel):
    online: bool
    latency_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    message: Optional[str] = None


class StatusResult(BaseModel):
    internet: InternetStatus
    local_ip: Optional[str] = None
    public_ip: Optional[str] = None
    gateway: Optional[str] = None
    dns_server: Optional[str] = None


class LocalIpResult(BaseModel):
    local_ip: Optional[str] = None
    message: Optional[str] = None


class PublicIpResult(BaseModel):
    public_ip: Optional[str] = None
    message: Optional[str] = None


class GatewayResult(BaseModel):
    gateway: Optional[str] = None
    message: Optional[str] = None


class PingResult(BaseModel):
    host: str
    status: Literal["reachable", "unreachable"]
    latency_ms: Optional[float] = None
    packet_loss_percent: float = 100.0
    packets_sent: int = 0
    packets_received: int = 0
    message: Optional[str] = None


class DnsResult(BaseModel):
    hostname: str
    status: Literal["resolved", "failed"]
    addresses: list[str] = Field(default_factory=list)
    dns_server: Optional[str] = None
    response_time_ms: Optional[float] = None
    message: Optional[str] = None


class TracerouteHop(BaseModel):
    hop: int
    address: Optional[str] = None
    latency_ms: Optional[float] = None


class TracerouteResult(BaseModel):
    target: str
    status: Literal["completed", "incomplete", "failed"]
    hops: list[TracerouteHop] = Field(default_factory=list)
    message: Optional[str] = None


class PortCheckResult(BaseModel):
    host: str
    port: int
    status: Literal["open", "closed", "timeout", "error"]
    response_time_ms: Optional[float] = None
    message: Optional[str] = None
