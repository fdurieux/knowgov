"""The worker's network check (harness/worker.py ``network``, ``loopback_only`` in its attestation) on a
fake sysfs and procfs: down tunnel devices beside lo pass, as Docker Desktop's kernel creates them in a
``network_mode: none`` container; an interface up, a route over anything but lo, CAP_NET_ADMIN held or
anything unreadable fail. The real worker's attestation is proven in the stack job (tools/check_worker.py
and demo.yml's loosened workers)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import worker  # noqa: E402

LO, DOWN, UP = "0x9", "0x80", "0x1003"   # IFF_UP|IFF_LOOPBACK; IFF_NOARP, down; IFF_UP|IFF_BROADCAST|IFF_MULTICAST
ROUTE_HEADER = "Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\t\tMTU\tWindow\tIRTT"
V6_LO = "00000000000000000000000000000001 80 00000000000000000000000000000000 00 " \
        "00000000000000000000000000000000 00000000 00000001 00000000 80200001       lo"
NO_CAPS = "0000000000000000"
NET_ADMIN = f"{1 << worker.CAP_NET_ADMIN:016x}"


def _view(ifaces: dict, routes: list[str] = (), v6: list[str] | None = (V6_LO,), eff=NO_CAPS, bnd=NO_CAPS) -> dict:
    with tempfile.TemporaryDirectory() as td:
        sysfs, proc = Path(td) / "sys", Path(td) / "proc"
        (sysfs / "class" / "net").mkdir(parents=True)
        for name, flags in ifaces.items():
            if flags == "file":
                (sysfs / "class" / "net" / name).write_text("\n")
                continue
            (sysfs / "class" / "net" / name).mkdir()
            if flags is not None:
                (sysfs / "class" / "net" / name / "flags").write_text(flags + "\n")
        (proc / "net").mkdir(parents=True)
        (proc / "self").mkdir()
        (proc / "net" / "route").write_text("\n".join([ROUTE_HEADER, *routes]) + "\n")
        if v6 is not None:
            (proc / "net" / "ipv6_route").write_text("\n".join(v6) + "\n")
        (proc / "self" / "status").write_text(f"Name:\tpython\nCapInh:\t{NO_CAPS}\nCapPrm:\t{eff}\nCapEff:\t{eff}\n"
                                              f"CapBnd:\t{bnd}\nCapAmb:\t{NO_CAPS}\n")
        return worker.network(str(sysfs), str(proc))


def test_lo_alone_passes():
    v = _view({"lo": LO})
    assert v["ok"] and v["interfaces"] == {"lo": "up"} and v["routes"] == [] and not v["cap_net_admin"], v


def test_down_tunnel_devices_beside_lo_pass_as_docker_desktop_creates_them():
    v = _view({"lo": LO, "tunl0": DOWN, "gre0": DOWN, "sit0": DOWN, "ip6tnl0": DOWN, "ip_vti0": DOWN})
    assert v["ok"], v
    assert v["interfaces"]["tunl0"] == "down" and v["interfaces"]["lo"] == "up", v


def test_docker_desktop_4_48s_network_none_view_passes():
    # /sys/class/net in a network_mode none container on Docker Desktop 4.48.0, kernel 6.10.14-linuxkit
    seen = {n: DOWN for n in ("erspan0", "gre0", "gretap0", "ip6_vti0", "ip6gre0", "ip6tnl0", "ip_vti0", "sit0", "tunl0")}
    v = _view({**seen, "lo": LO, "bonding_masters": "file"})
    assert v["ok"] and "bonding_masters" not in v["interfaces"] and len(v["interfaces"]) == 10, v


def test_an_interface_up_fails():
    assert not _view({"lo": LO, "eth0": UP})["ok"]
    assert not _view({"lo": LO, "tunl0": DOWN, "gre0": UP})["ok"]


def test_a_down_device_with_a_route_fails():
    v = _view({"lo": LO, "tunl0": DOWN}, routes=["tunl0\t00000000\t010200C0\t0003\t0\t0\t0\t00000000\t0\t0\t0"])
    assert not v["ok"] and v["routes"] == ["route:tunl0"], v
    v6 = V6_LO.replace("      lo", "   tunl0")
    v = _view({"lo": LO, "tunl0": DOWN}, v6=[V6_LO, v6])
    assert not v["ok"] and v["routes"] == ["ipv6_route:tunl0"], v


def test_cap_net_admin_effective_or_in_the_bounding_set_fails():
    assert not _view({"lo": LO}, eff=NET_ADMIN, bnd=NET_ADMIN)["ok"]
    assert not _view({"lo": LO}, bnd=NET_ADMIN)["ok"], "a process here could regain it"
    assert _view({"lo": LO}, eff=f"{(1 << 21) - 1 - (1 << 12):016x}")["cap_net_admin"] is False


def test_whatever_cannot_be_read_fails_closed():
    assert not _view({"lo": LO, "tunl0": None})["ok"], "a device whose flags are unread counts as up"
    with tempfile.TemporaryDirectory() as td:
        assert not worker.network(str(Path(td) / "nosys"), str(Path(td) / "noproc"))["ok"]
    assert _view({"lo": LO}, v6=None)["ok"], "a kernel without IPv6 has no ipv6_route table and no IPv6 route"


def test_the_attestation_carries_the_view_and_its_check():
    with tempfile.TemporaryDirectory() as td:
        a = worker.attest({}, sys_root=str(Path(td) / "nosys"), proc_root=str(Path(td) / "noproc"))
    assert a["checks"]["loopback_only"] is False and a["interfaces"] is None and a["routes"] is None and a["cap_net_admin"]
