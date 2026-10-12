"""Deliverable 3: audit logging without a second PII store (Monday variant).

Logs the actor, action, resource, outcome, and a short hash of the
payload -- never the raw message, which may carry health information or
a national ID number. An audit trail that is itself a second copy of
personal data has not actually reduced anything. redact_then_hash.py in
this same folder adds redaction of what little text does get hashed;
this file is the simpler sibling kept for the "hash only" worked example
the Deliverable 3 self-assessment distinguishes from "redact only".
"""
import hashlib
import json
import time


def audit(actor: str, action: str, resource: str, ok: bool, payload: str | None = None) -> None:
    """Print one structured JSON line -- indexable by a log collector,
    unlike an interpolated sentence a human would have to grep for."""
    row = {
        "ts": int(time.time()),
        "actor": actor,
        "action": action,
        "resource": resource,
        "ok": ok,
        # A short correlatable token, not the sentence itself.
        "payload_sha": hashlib.sha256((payload or "").encode()).hexdigest()[:16],
    }
    print(json.dumps(row))


if __name__ == "__main__":
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        audit(
            "partner_clinic", "check_stock", "KSM-01", True,
            "national id 12345678 fever two days",
        )
    row = json.loads(buf.getvalue())
    # The sentence must never reach the log, only a correlatable token.
    assert "12345678" not in buf.getvalue()
    assert row["actor"] == "partner_clinic" and row["ok"] is True
    assert len(row["payload_sha"]) == 16

    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        audit(
            "partner_clinic", "check_stock", "KSM-01", True,
            "national id 12345678 fever two days",
        )
    assert json.loads(buf2.getvalue())["payload_sha"] == row["payload_sha"]
    print("audit_log OK", row["action"], row["payload_sha"])
