# Current IPv6 availability — 4 November 2026

The [subsequent gateway inspection](router-ipv6-inspection.md) finds a managed
user-login portal, no public router IPv6 status, Router Discovery enabled and
no Windows IPv6-disable registry override. Administrative network confirmation
is the next missing evidence; the upstream cause remains unverified.

**The current Wi-Fi connection has no usable direct IPv6 Internet path.** The
adapter supports IPv6, but Windows has only a link-local address on Wi-Fi, no
global IPv6 address there, and no IPv6 default route listed. This is a current
network-availability finding, not a classifier result.

The bounded read-only diagnostic completed at2026-11-04T11:56:09.5154863Z:

| Check | Actual result |
| --- | --- |
| Wi-Fi state / IPv6 support | Up / enabled |
| Wi-Fi IPv6 addresses | One link-local, zero global candidates |
| Listed IPv6 default routes | Zero |
| Explicit DNS AAAA query for `www.youtube.com` | Eight IPv6 addresses |
| Ordinary system resolver | Eight IPv4, zero IPv6 addresses returned |
| TCP443 to one resolved YouTube IPv4 address | Connected |
| TCP443 to one explicitly resolved YouTube IPv6 address | Failed: Windows10051, `NetworkUnreachable` |

The TCP checks ran outside sandbox network restrictions, each capped at three
seconds. They test reachability, not QUIC/UDP behavior or packet-to-model latency.
They sent connection handshakes only; no HTTP content request, packet capture or
network-setting change occurred. No client addresses are exported in the report.

An initial Python resolver query returned no IPv6 records. The explicit Windows
DNS query nevertheless returned AAAA records, so that initial result must not
be interpreted as YouTube lacking IPv6 DNS support. CIM-based Windows inventory
was unavailable in the tool context; native `route.exe` and .NET interface
enumeration supplied the configuration evidence instead. Their results agree
with the direct IPv6 connection failure.

This explains the lack of IPv6 examples in the latest ordinary YouTube visit.
It does not identify whether the router, ISP, or another local network condition
is responsible. Earlier recorded IPv6 sessions remain valid historical evidence;
today's result does not rewrite them or establish a permanent limitation of this
laptop. The classifier's earlier errors and failed experiments remain unresolved.

## Consequence for collection

The [family collection scope](family-coverage-plan.md) stays stopped. Repeating
the visit on the unchanged current connection is not a supported way to obtain
the required IPv6 training examples. Do not alter captured sizes, relabel IPv4
flows, relax the gate or automatically reopen the stopped slot.

The next network investigation is the router's IPv6 WAN/LAN status and whether
the ISP currently supplies IPv6, or confirmation of another network with working
IPv6. Router/ISP cause is unverified; no router login, firmware/configuration
change, adapter toggle, DNS change or connection reset was attempted. Restoring
IPv6 would permit a connectivity recheck, then a separately declared collection
scope. It would not by itself validate the model or justify deployment.

## Reproduce and evidence

From the repository directory on Windows, use a fresh output path:

```powershell
./scripts/check_ipv6_network.ps1 -Output experiments/network-ipv6-recheck/report.json
```

Existing outputs are refused before any probes, so the original evidence stays
intact. PowerShell parsing passed and a repeat invocation against the existing
file was verified to refuse and preserve its hash. The actual two-family probe
completed successfully as a diagnostic (including the recorded IPv6 failure).
No Python application source changed; the previous403-test checkpoint remains
the applicable application-software evidence, not a newly rerun suite.

Private report: `experiments/network-ipv6-check-v1/report.json`.
Report SHA-256:
`8ef2ef5b8ec37462bfb4cdcdcdd892c5c26ddcf1ea55eb9f4056b8c0f26e15ac`.
Script SHA-256:
`dc3e8276751e261df37adee9054f515de1f1ef24c97aa25d96a595ffd2600b69`.
The report also records this source hash, timestamp, interface counts, route
count, DNS counts, socket error and scope limitations. No external publication
or new model artifact follows from this network diagnostic.
