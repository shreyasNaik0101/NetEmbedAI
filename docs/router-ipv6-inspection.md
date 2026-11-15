# Gateway and client IPv6 inspection — 4 November 2026

The current gateway exposes an institution-branded **24Online user login
portal**. Its public pages do not expose router WAN/LAN IPv6 status. The router
model, upstream ISP and their IPv6 configuration remain unverified. Identifying
a login portal does not establish which device or provider lacks IPv6 support.

The laptop-side checks found Wi-Fi Router Discovery enabled and no
`DisabledComponents` registry override. The adapter supports IPv6. These checks
found no obvious client-side IPv6-disable override; they are not an exhaustive
audit of firewall, driver, VPN or host policy. Managed/other-stateful address
configuration flags are disabled in the current interface state; this alone is
not a fault and is not an instruction to enable DHCPv6 manually.

Together with the [previous connectivity check](network-ipv6-check.md), the
evidence is: working IPv4; no global Wi-Fi IPv6 address/default route; YouTube
AAAA DNS records present; explicit IPv6 connection fails NetworkUnreachable.
The connection currently cannot supply the IPv6 training examples. This does
not locate the cause between network provisioning, router advertisements,
upstream connectivity or another local policy.

## What was inspected

- Read the Wi-Fi gateway/DNS/DHCP configuration using .NET.
- Requested the gateway root, then the exact login path linked by that response.
  Each request was bounded to four seconds and128KiB. No arbitrary paths/ports
  were scanned, HTTP redirects followed, form submitted or credentials supplied.
- Read selected `netsh interface ipv6 show interface` settings and checked for
  the Windows IPv6 `DisabledComponents` override.
- Kept private gateway identity/page responses in ignored local evidence;
  client address/MAC details are not included in this document.

The HTTPS gateway probe encountered a self-signed certificate. Certificate
verification was not disabled. The HTTP public page supplied the observed login
path. That certificate result is not an explanation of missing IPv6 routing.
Wi-Fi SSID enumeration required elevation and was unavailable in the initial
query; the diagnosis does not infer a particular SSID or upstream provider.

No model was trained, no packet capture started and no host/router/DNS setting
changed. The stopped [collection scope](family-coverage-plan.md) remains closed.
Application source is unchanged; no new403-test-suite result is claimed.

## Precise next dependency

The network administrator needs to confirm whether native IPv6 is provisioned
on this Wi-Fi, whether clients should receive a global address/default route,
and whether router advertisements reach clients. Administrative status is not
available through the public user-login page. No admin login or private router
credentials were requested or guessed. An authenticated administrator view or
their confirmation is needed to distinguish the remaining causes.

A short message the user can send themselves:

> Does this Wi-Fi currently provide IPv6? IPv4 Internet works, but my laptop has
> no global IPv6 address or IPv6 default route. Router Discovery is enabled and
> IPv6 connections fail with Windows error10051. Should clients on this network
> receive IPv6 connectivity?

No message was sent. A network change or confirmed restoration should first
receive a fresh connectivity check, not another classifier recording under the
closed scope. Working IPv6 would address acquisition feasibility; dependable
model recognition would still require its separate training/evaluation work.

## Local evidence

Private directory: `experiments/router-ipv6-inspection-v1/`.
`gateway-web-check.json` records bounded HTTP/HTTPS results;
`portal-page-check.json` records login identification without field values;
`client-settings-check.json` records selected local settings.
`inspection-summary.json` binds all report/response hashes and explicit unknowns.
Its SHA-256 is
`f3a90dcef899a8d94c1a72ba41fadb4091f65ca096fb0588cf1f328f4e707675`.
Raw portal HTML remains private and is not a classifier input or published asset.
