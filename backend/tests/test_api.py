"""API tests. All network operations are mocked."""

from app.api import routes
from app.schemas import (
    DnsResult,
    InternetStatus,
    PingResult,
    PortCheckResult,
    StatusResult,
    TracerouteHop,
    TracerouteResult,
)


def test_status(client, monkeypatch):
    monkeypatch.setattr(
        routes.status,
        "get_status",
        lambda: StatusResult(
            internet=InternetStatus(online=True, latency_ms=18.0, packet_loss_percent=0.0),
            local_ip="192.168.1.34",
            public_ip=None,
            gateway="192.168.1.1",
            dns_server="8.8.8.8",
        ),
    )
    body = client.get("/api/network/status").json()
    assert body["internet"]["online"] is True
    assert body["public_ip"] is None  # API failure must not break the dashboard
    assert body["gateway"] == "192.168.1.1"


def test_local_ip(client, monkeypatch):
    monkeypatch.setattr(routes.local_network, "get_local_ip", lambda: "192.168.1.34")
    assert client.get("/api/network/local-ip").json()["local_ip"] == "192.168.1.34"


def test_public_ip_unavailable(client, monkeypatch):
    monkeypatch.setattr(routes.public_ip, "get_public_ip", lambda: None)
    response = client.get("/api/network/public-ip")
    assert response.status_code == 200
    assert response.json()["public_ip"] is None
    assert "could not be retrieved" in response.json()["message"]


def test_gateway_not_found(client, monkeypatch):
    monkeypatch.setattr(routes.local_network, "get_default_gateway", lambda: None)
    assert client.get("/api/network/gateway").json()["message"] == "Gateway could not be detected"


def test_ping(client, monkeypatch):
    monkeypatch.setattr(
        routes.ping,
        "ping_host",
        lambda target: PingResult(
            host=target,
            status="reachable",
            latency_ms=24.0,
            packet_loss_percent=0.0,
            packets_sent=4,
            packets_received=4,
        ),
    )
    response = client.post("/api/network/ping", json={"target": " Google.com "})
    assert response.status_code == 200
    assert response.json()["host"] == "google.com"
    assert response.json()["latency_ms"] == 24.0


def test_ping_rejects_command_injection(client, monkeypatch):
    called = []
    monkeypatch.setattr(routes.ping, "ping_host", lambda t: called.append(t))
    for payload in ["google.com; rm -rf /", "8.8.8.8 && whoami", "$(id)", "-c 100 x.com", ""]:
        response = client.post("/api/network/ping", json={"target": payload})
        assert response.status_code == 422, payload
        assert isinstance(response.json()["detail"], str)
    assert called == []


def test_invalid_ip_message(client):
    response = client.post("/api/network/traceroute", json={"target": "999.999.1.1"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid hostname or IP address."


def test_dns(client, monkeypatch):
    monkeypatch.setattr(
        routes.dns_lookup,
        "lookup",
        lambda hostname: DnsResult(
            hostname=hostname,
            status="resolved",
            addresses=["142.250.1.1"],
            dns_server="8.8.8.8",
            response_time_ms=21.0,
        ),
    )
    body = client.post("/api/network/dns", json={"hostname": "google.com"}).json()
    assert body["addresses"] == ["142.250.1.1"]
    assert body["dns_server"] == "8.8.8.8"


def test_dns_rejects_ip(client):
    response = client.post("/api/network/dns", json={"hostname": "8.8.8.8"})
    assert response.status_code == 422
    assert "hostname" in response.json()["detail"].lower()


def test_traceroute(client, monkeypatch):
    monkeypatch.setattr(
        routes.traceroute,
        "run_traceroute",
        lambda target: TracerouteResult(
            target=target,
            status="completed",
            hops=[TracerouteHop(hop=1, address="192.168.1.1", latency_ms=2.0)],
        ),
    )
    body = client.post("/api/network/traceroute", json={"target": "google.com"}).json()
    assert body["hops"][0]["address"] == "192.168.1.1"


def test_port_check(client, monkeypatch):
    monkeypatch.setattr(
        routes.port_check,
        "tcp_check",
        lambda host, port: PortCheckResult(host=host, port=port, status="open", response_time_ms=3.0),
    )
    body = client.post("/api/network/port-check", json={"host": "192.168.1.1", "port": 80}).json()
    assert body["status"] == "open" and body["port"] == 80


def test_port_out_of_range(client):
    for port in (0, 65536, -5, "abc"):
        response = client.post("/api/network/port-check", json={"host": "192.168.1.1", "port": port})
        assert response.status_code == 422, port
        assert "1 and 65535" in response.json()["detail"]


def test_unexpected_error_is_not_leaked(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    def boom(target):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(routes.ping, "ping_host", boom)
    local_client = TestClient(app, raise_server_exceptions=False)
    response = local_client.post("/api/network/ping", json={"target": "google.com"})
    assert response.status_code == 500
    assert "secret" not in response.text
