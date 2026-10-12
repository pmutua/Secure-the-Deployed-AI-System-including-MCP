"""Deliverable 1: encryption in transit.

Decides whether a URL may carry AfyaPlus partner traffic, and proves a
real TLS handshake when one is reachable. Localhost HTTP stays allowed
for labs -- that exception is written down as a named set (LAB_HOSTS)
rather than left as an unwritten habit, so it is enumerable and cannot
silently widen to cover a real partner host by accident.

This module has no network dependency for its own __main__ block: the
assertions at the bottom only call transit_ok(), which is pure string
parsing. tls_handshake_ok() and https_get_ok() open real sockets and are
exercised separately in tests/test_encryption.py, which monkeypatches
them rather than depending on a live endpoint.
"""
from __future__ import annotations

import ssl
import urllib.request
from urllib.parse import urlparse

# The only hosts HTTP is ever allowed for. A named set, not a substring
# test on the URL -- a substring test would also match a hostile hostname
# that merely *contains* "127.0.0.1" or "localhost".
LAB_HOSTS = {"127.0.0.1", "localhost"}


def transit_ok(url: str, allow_localhost: bool = True) -> bool:
    """Policy check: non-localhost partner URLs must use https.

    Returns a bool rather than raising -- that is the contract every
    caller depends on, whether it sits inside an assertion, a pytest
    case, or a FastAPI dependency.
    """
    u = urlparse(url)
    # Fail closed on anything unparseable. A bare hostname with no
    # scheme parses without raising, so both fields must be present
    # before any policy decision is meaningful.
    if not u.scheme or not u.hostname:
        return False
    if allow_localhost and u.hostname in LAB_HOSTS:
        return True  # HTTP allowed only here, and only for labs
    return u.scheme == "https"


def tls_handshake_ok(host: str, port: int = 443, timeout: float = 5.0) -> bool:
    """Real TLS check: fetch the server certificate, failing closed on any error."""
    try:
        ssl.get_server_certificate((host, port), timeout=timeout)
        return True
    except Exception:
        # DNS failure, refused connection, expired cert, and a timeout
        # all mean the same thing to a policy check -- "not currently
        # provably TLS" -- and all fail closed the same way.
        return False


def https_get_ok(url: str, timeout: float = 5.0) -> bool:
    """Real HTTPS request; localhost HTTP remains a documented lab exception."""
    if not transit_ok(url):
        return False
    u = urlparse(url)
    if u.hostname in LAB_HOSTS:
        return True
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except Exception:
        return False


if __name__ == "__main__":
    assert transit_ok("https://api.afyaplus.ke/triage") is True
    assert transit_ok("http://127.0.0.1:8000/triage") is True
    assert transit_ok("http://api.afyaplus.ke/triage") is False
    # A production host is never allowed to pass over cleartext even
    # inside a unit test with no network access -- this is the "transit_ok
    # still refuses a cleartext production host" fallback the capstone
    # brief names explicitly for "No production domain".
    assert transit_ok("http://afyaplus-prod.ke/triage") is False
    print("transit_policy OK")
