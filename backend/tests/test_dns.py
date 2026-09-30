import dns.exception
import dns.resolver
import dns.rrset

from app.services import dns_lookup


def _rrset(rdtype, *addresses):
    return dns.rrset.from_text("example.com.", 300, "IN", rdtype, *addresses)


def test_extract_addresses_from_rrset():
    rrset = _rrset("A", "93.184.216.34", "93.184.216.35")
    assert dns_lookup.extract_addresses(rrset) == ["93.184.216.34", "93.184.216.35"]


def test_extract_addresses_deduplicates_and_ignores_non_address_records():
    txt = dns.rrset.from_text("example.com.", 300, "IN", "TXT", '"hello"')
    assert dns_lookup.extract_addresses(txt) == []
    assert dns_lookup.extract_addresses([*_rrset("A", "1.1.1.1"), *_rrset("A", "1.1.1.1")]) == [
        "1.1.1.1"
    ]


class FakeResolver:
    nameservers = ["8.8.8.8"]
    timeout = 0
    lifetime = 0
    behaviour: dict = {}

    def resolve(self, hostname, rdtype):
        outcome = self.behaviour[rdtype]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _patch(monkeypatch, **behaviour):
    FakeResolver.behaviour = behaviour
    monkeypatch.setattr(dns_lookup.dns.resolver, "Resolver", FakeResolver)


def test_lookup_success(monkeypatch):
    _patch(
        monkeypatch,
        A=_rrset("A", "142.250.1.1", "142.250.1.2"),
        AAAA=dns.resolver.NoAnswer(),
    )
    result = dns_lookup.lookup("example.com")
    assert result.status == "resolved"
    assert result.addresses == ["142.250.1.1", "142.250.1.2"]
    assert result.dns_server == "8.8.8.8"
    assert result.response_time_ms is not None


def test_lookup_includes_ipv6(monkeypatch):
    _patch(monkeypatch, A=_rrset("A", "1.1.1.1"), AAAA=_rrset("AAAA", "2606:4700::1111"))
    assert dns_lookup.lookup("example.com").addresses == ["1.1.1.1", "2606:4700::1111"]


def test_lookup_nxdomain(monkeypatch):
    _patch(monkeypatch, A=dns.resolver.NXDOMAIN(), AAAA=dns.resolver.NXDOMAIN())
    result = dns_lookup.lookup("nope.invalid")
    assert result.status == "failed"
    assert result.message == "Hostname could not be resolved."


def test_lookup_timeout(monkeypatch):
    _patch(monkeypatch, A=dns.exception.Timeout(), AAAA=dns.exception.Timeout())
    result = dns_lookup.lookup("example.com")
    assert result.status == "failed"
    assert "did not respond" in result.message


def test_lookup_no_nameservers(monkeypatch):
    _patch(monkeypatch, A=dns.resolver.NoNameservers(), AAAA=dns.resolver.NoNameservers())
    assert dns_lookup.lookup("example.com").status == "failed"
