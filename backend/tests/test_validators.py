import pytest

from app.validators import (
    is_valid_hostname,
    is_valid_ip,
    is_valid_port,
    validate_hostname,
    validate_target,
)


@pytest.mark.parametrize("value", ["8.8.8.8", "192.168.1.1", "::1", "2001:4860:4860::8888"])
def test_valid_ips(value):
    assert is_valid_ip(value)


@pytest.mark.parametrize(
    "value", ["999.1.1.1", "1.2.3", "", "abc", "1.1.1.1; ls", "fe80::1%eth0", "-1.1.1.1"]
)
def test_invalid_ips(value):
    assert not is_valid_ip(value)


@pytest.mark.parametrize(
    "value", ["google.com", "localhost", "sub.example.co.uk", "a-b.example.com", "example.com."]
)
def test_valid_hostnames(value):
    assert is_valid_hostname(value)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "-bad.com",
        "bad-.com",
        "a..b",
        "exa mple.com",
        "google.com; rm -rf /",
        "google.com && whoami",
        "$(whoami).com",
        "`id`.com",
        "a|b.com",
        "under_score.com",
        "999.999.999.999",
        "-c 100 google.com",
        "a" * 64 + ".com",
        ("a" * 60 + ".") * 5 + "com",
    ],
)
def test_invalid_hostnames(value):
    assert not is_valid_hostname(value)


@pytest.mark.parametrize("port", [1, 80, 443, 65535])
def test_valid_ports(port):
    assert is_valid_port(port)


@pytest.mark.parametrize("port", [0, -1, 65536, "80", None, 1.5, True])
def test_invalid_ports(port):
    assert not is_valid_port(port)


def test_validate_target_normalises():
    assert validate_target("  Google.COM ") == "google.com"
    assert validate_target("8.8.8.8") == "8.8.8.8"


def test_validate_target_punycode():
    assert validate_target("türkiye.gov.tr").startswith("xn--")


@pytest.mark.parametrize("value", ["", "   ", "bad host", "a;b"])
def test_validate_target_rejects(value):
    with pytest.raises(ValueError):
        validate_target(value)


def test_validate_hostname_rejects_ip():
    with pytest.raises(ValueError):
        validate_hostname("8.8.8.8")
