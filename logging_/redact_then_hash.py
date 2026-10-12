"""Deliverable 3: the structured audit trail -- redact first, then hash.

Stacking both correctly means redacting FIRST and hashing the CLEANED
text: hashing the original would make the digest a stable fingerprint of
the unredacted sentence, so two identical unredacted messages would
still be linkable through the very log this file exists to sanitise.

Carries actor, action, resource, outcome, and a trace_id when the caller
has one -- app/main.py's /triage route calls write_audit_line() with its
own trace id so a request can be followed end to end without ever
writing the patient's message to disk in the clear.
"""
import hashlib
import json
import time
from pathlib import Path

from logging_.redact import redact

LOG = Path("logging_/logs/audit_stacked.jsonl")


def write_audit_line(
    actor: str,
    action: str,
    resource: str,
    outcome: bool,
    payload: str = "",
    trace_id: str | None = None,
) -> dict:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    cleaned = redact(payload)
    row = {
        "ts": int(time.time()),
        "actor": actor,
        "action": action,
        "resource": resource,
        "outcome": "ok" if outcome else "denied",
        "trace_id": trace_id,
        "payload_redacted": cleaned,
        # Hashed over the CLEANED text, not the original -- see the
        # module docstring. Truncated to 16 hex chars: enough entropy to
        # correlate repeats within a day's traffic, short enough that a
        # human scanning the log isn't dominated by an unreadable digest.
        "payload_sha": hashlib.sha256(cleaned.encode()).hexdigest()[:16],
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


if __name__ == "__main__":
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("", encoding="utf-8")
    result = write_audit_line(
        "partner_clinic", "check_stock", "KSM-01", True,
        "national id 87654321 Bearer eyJ.demo",
        trace_id="demo-trace-1",
    )
    assert "87654321" not in result["payload_redacted"]
    assert "eyJ" not in result["payload_redacted"]
    assert len(result["payload_sha"]) == 16
    assert result["outcome"] == "ok"
    print("redact_then_hash OK", result)
