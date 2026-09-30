from app.services import local_network as ln

WINDOWS = """IPv4 Route Table
===========================================================================
Active Routes:
Network Destination        Netmask          Gateway       Interface  Metric
          0.0.0.0          0.0.0.0      192.168.1.1     192.168.1.34     25
          0.0.0.0          0.0.0.0      10.0.0.1        10.0.0.5         50
        127.0.0.0        255.0.0.0         On-link         127.0.0.1    331
===========================================================================
Persistent Routes:
  Network Address          Netmask  Gateway Address  Metric
          0.0.0.0          0.0.0.0      172.16.0.1  Default
"""

PROC = """Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\t\tMTU\tWindow\tIRTT
eth0\t00000000\t0100A8C0\t0003\t0\t0\t100\t00000000\t0\t0\t0
eth0\t0000A8C0\t00000000\t0001\t0\t0\t100\t00FFFFFF\t0\t0\t0
wlan0\t00000000\t0100000A\t0003\t0\t0\t600\t00000000\t0\t0\t0
"""


def test_windows_route_print_lowest_metric():
    assert ln.parse_windows_route_print(WINDOWS) == "192.168.1.1"


def test_windows_route_print_none():
    assert ln.parse_windows_route_print("nothing here") is None


def test_proc_net_route():
    assert ln.parse_proc_net_route(PROC) == "192.168.0.1"


def test_proc_net_route_no_default():
    assert ln.parse_proc_net_route("Iface\tDestination\n") is None


def test_ip_route():
    assert ln.parse_ip_route("default via 192.168.1.1 dev wlan0 proto dhcp metric 600") == "192.168.1.1"
    assert ln.parse_ip_route("") is None


def test_macos_route():
    text = "   route to: default\n destination: default\n     gateway: 192.168.1.1\n"
    assert ln.parse_macos_route(text) == "192.168.1.1"
