"""Deliverable 4: a data subject rights lookup that answers with counts,
never content.

Why not plain SHA-256: this capstone draws clinic identifiers from a set
of exactly three (KSM-01, VIH-01, HBA-01 -- see
access_control/clinics_allowlist.json). A plain sha256(clinic_id) digest
is reversed in three guesses: hash all three candidates and compare.
Low-cardinality input turns a "one-way" hash into a lookup table with
extra steps. HMAC with a pepper that never leaves the server is what
keeps the digest a real one-way step.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path

DEFAULT_FIXTURE = Path("dpa/fixtures/subjects.json")


def pepper() -> bytes:
    """Return the secret pepper as bytes, or exit the program if none is set."""
    # Fail loud rather than silently hashing with an empty key -- an
    # empty-keyed HMAC produces stable, guessable digests and looks
    # exactly like a working implementation.
    val = os.getenv("SUBJECT_PEPPER") or os.getenv("JWT_SECRET") or ""
    if not val.strip():
        print("missing SUBJECT_PEPPER (and no JWT_SECRET fallback)")
        raise SystemExit(1)
    return val.encode()


def subject_key(clinic_id: str) -> str:
    """Turn a clinic ID into its peppered HMAC-SHA256 digest (first 16 hex chars)."""
    return hmac.new(pepper(), clinic_id.encode(), hashlib.sha256).hexdigest()[:16]


def lookup(clinic_id: str, fixture: Path = DEFAULT_FIXTURE) -> dict:
    """Answer 'what do you hold about this clinic?' with a count only."""
    rows = json.loads(fixture.read_text(encoding="utf-8"))
    want = subject_key(clinic_id)
    n = sum(1 for r in rows if r.get("subject_hash") == want)
    # A count and a kind, never the row's message text.
    return {"found": n > 0, "n_events": n}


def main() -> None:
    print(lookup("KSM-01"))  # a real clinic with rows in the fixture -> found
    print(lookup("HBA-01"))  # a real clinic with zero rows -> not found


if __name__ == "__main__":
    main()
