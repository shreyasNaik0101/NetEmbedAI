"""Connection pseudonyms used only for explicit local evaluation, never features."""

import hashlib
import hmac
import ipaddress
import json

VERSION = "tuple-hmac-sha256-v1"


def endpoint(address, port):
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    port = int(port)
    if not 1 <= port <= 65535:
        raise ValueError("invalid endpoint port")
    return str(ip), port


def parse_endpoint(value):
    if not isinstance(value, str):
        raise ValueError("endpoint field unavailable")
    if value.startswith("["):
        address, port = value[1:].rsplit("]:", 1)
    else:
        if value.count(":") != 1:
            raise ValueError("expected an IPv4 endpoint or bracketed IPv6 endpoint")
        address, port = value.rsplit(":", 1)
    return endpoint(address, port)


def connection_token(first, second, salt):
    if not isinstance(salt, str) or len(salt) != 64:
        raise ValueError("invalid session matching key")
    key = bytes.fromhex(salt)
    pair = sorted((endpoint(*first), endpoint(*second)))
    message = json.dumps(pair, separators=(",", ":")).encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()
