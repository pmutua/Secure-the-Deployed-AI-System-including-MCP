"""Deliverable 3: redact before anything reaches disk.

Strips obvious tokens and identity-shaped numbers before the text is
even written, so a log line is safe to read rather than merely safe to
search. This stacks with redact_then_hash.py -- hashing gives
correlation, redaction limits what a human reader (or a support bundle,
or a backup) ever sees.

Every pattern below is Kenya-facing and every comment records the false
positive it exists to avoid -- a redactor that eats its own timestamps
or leaves a phone number's prefix behind is worse than no redactor,
because it creates false confidence.
"""
import json
import re
from pathlib import Path

# Bearer token: case-insensitive, since header capitalisation varies by
# client -- a redactor that only matches "Bearer" misses "bearer".
BEARER = re.compile(r"Bearer\s+\S+", re.I)

# Kenyan national identity number: exactly 8 digits, word-bounded. NOT a
# 7-to-10-digit catch-all -- that range also matches a Unix timestamp
# (10 digits), and a redactor that eats its own timestamps produces logs
# nobody can order.
KENYA_ID = re.compile(r"\b\d{8}\b")

# Kenyan mobile number: 07XXXXXXXX or +2547XXXXXXXX.
PHONE = re.compile(r"(?:\+254|0)7\d{8}\b")

# M-Pesa confirmation code: a letter followed by nine alphanumerics.
# Anchored on the leading letter so a bare 10-digit epoch timestamp
# never matches this pattern either.
MPESA = re.compile(r"\b[A-Z][A-Z0-9]{9}\b")

LOG = Path("logging_/logs/audit.jsonl")


def redact(text: str) -> str:
    """Strip tokens and identity-shaped numbers, in an order that matters.

    PHONE runs before KENYA_ID on purpose: a Kenyan phone number's last
    eight digits alone would also match KENYA_ID. Redacting the phone
    first removes the whole number in one pass.
    """
    text = BEARER.sub("Bearer [REDACTED]", text)
    text = PHONE.sub("[REDACTED_PHONE]", text)
    text = MPESA.sub("[REDACTED_MPESA]", text)
    text = KENYA_ID.sub("[REDACTED_ID]", text)
    return text


def write_audit(actor: str, action: str, resource: str, payload: str) -> str:
    """Redact, then append one JSON object per line (jsonl).

    Append mode, not truncate: an audit log that rewrites itself on
    every call has destroyed the record it exists to keep. actor/
    action/resource stay in cleartext deliberately -- they ARE the
    audit, and redacting them would leave a file that proves nothing.
    """
    LOG.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "actor": actor,
        "action": action,
        "resource": resource,
        "payload": redact(payload),
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row["payload"]


if __name__ == "__main__":
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("", encoding="utf-8")
    stored = write_audit(
        "partner_clinic", "check_stock", "KSM-01",
        "id 12345678 phone 0712345678 code SH45K7L9M2 "
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.aaa",
    )
    blob = LOG.read_text(encoding="utf-8")
    assert "12345678" not in blob
    assert "0712345678" not in blob
    assert "eyJhbGci" not in blob
    # A ten-digit epoch timestamp is not an identity number and must
    # survive untouched.
    assert redact("ts 1724000000 event") == "ts 1724000000 event"
    print("redact OK", stored)
