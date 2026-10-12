"""Deliverable 2: clinic allowlist on a stub stock tool.

Adversarial input is not only override prose. A partner calling
check_stock with clinic_id="*" is attempting bulk extraction using a
perfectly valid-looking request -- no override phrase for
injection_guard.py to catch. logistics_mcp_secure.py applies this exact
normalise-then-decide idea directly to the real check_stock MCP tool
when the caller's role is partner_clinic; this file is the standalone,
protocol-free worked example used by tests/test_access_control.py.

Why "*" specifically: it is the conventional glob/select-all token in
shells, SQL LIKE patterns, and many query APIs. A caller sends it hoping
the field is interpreted as a pattern ("give me every clinic") rather
than a literal identifier. check_stock() never gives "*" special
meaning -- clinic_id is normalised and compared by exact string equality
only, so "*" is just another string that fails membership.

Design rules, in the order they matter operationally:
  1. Reject before you look anything up -- otherwise response *timing*
     leaks which identifiers exist, building an enumeration oracle.
  2. An empty or unreadable allowlist is a 500 (config failure), never a
     400 (a clean refusal) -- a 400 on every request would make a broken
     deployment look like it is working correctly.
  3. Normalise both the stored identifiers and the incoming one.
"""
from __future__ import annotations

import json
from pathlib import Path

ALLOWLIST_PATH = Path("access_control/clinics_allowlist.json")

# Stub stock data for the three known clinics -- enough to prove the
# allowlist gate. logistics_mcp_secure.py is the real check_stock tool,
# wired to the real clinics.json; this file is a security-test fixture.
STOCK = {
    "KSM-01": {"amoxicillin": 40, "ors_sachets": 120},
    "VIH-01": {"amoxicillin": 12, "ors_sachets": 8},
    "HBA-01": {"amoxicillin": 25, "ors_sachets": 60},
}


def load_known(path: Path = ALLOWLIST_PATH) -> frozenset[str]:
    """Read and normalise the allowlist; raise if it is missing or empty."""
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = {str(c).strip().upper() for c in data.get("clinics", [])}
    if not ids:
        raise ValueError("clinics_allowlist.json has no clinics")
    return frozenset(ids)


def check_stock(clinic_id: str, item: str, allowlist_path: Path = ALLOWLIST_PATH) -> dict:
    try:
        known = load_known(allowlist_path)
    except (OSError, ValueError, json.JSONDecodeError):
        # Configuration failure, not a security decision: fail closed
        # with a 500 so the outage is visible rather than silently
        # denying every caller with a 400 that looks like normal traffic.
        return {"error": "allowlist unavailable", "code": 500}

    cid = (clinic_id or "").strip().upper()
    if cid not in known:
        # "*", "", and any id outside the three known clinics all land
        # here -- reject before the STOCK lookup even runs.
        return {"error": "unknown clinic_id", "code": 400}

    qty = STOCK.get(cid, {}).get(item, 0)
    return {"clinic": cid, "item": item, "qty": qty}


if __name__ == "__main__":
    import tempfile

    result = check_stock("ksm-01", "amoxicillin")
    assert result == {"clinic": "KSM-01", "item": "amoxicillin", "qty": 40}

    # The bulk-extraction probe: "*" looks like a normal, schema-valid
    # request (no override prose for injection_guard.py to flag), so the
    # only thing standing between a partner and every clinic's stock is
    # the allowlist treating clinic_id as a literal, not a pattern.
    wildcard = check_stock("*", "amoxicillin")
    assert wildcard == {"error": "unknown clinic_id", "code": 400}

    with tempfile.TemporaryDirectory() as tmp:
        empty_path = Path(tmp) / "empty_allowlist.json"
        empty_path.write_text(json.dumps({"clinics": []}))
        empty_result = check_stock("KSM-01", "amoxicillin", allowlist_path=empty_path)
        assert empty_result == {"error": "allowlist unavailable", "code": 500}

    print("allowlist_stock OK: known clinic, wildcard refused, empty allowlist fails closed")
