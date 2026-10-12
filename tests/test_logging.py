# test_logging.py - Deliverable 3 evidence: redact-then-hash stacking,
# with assertions on the FILE that actually landed on disk, not just a
# function's return value -- a bug that redacts on the way out while
# writing the original would pass a check against the return value but
# not against what the jsonl actually holds.

from __future__ import annotations

from logging_.redact import redact
from logging_.redact_then_hash import write_audit_line


def test_redact_strips_bearer_token() -> None:
    assert "eyJhbGci" not in redact("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.aaa")


def test_redact_strips_kenyan_phone_number() -> None:
    assert "0712345678" not in redact("call 0712345678 now")


def test_redact_strips_eight_digit_national_id() -> None:
    assert "12345678" not in redact("national id 12345678")


def test_redact_does_not_eat_a_ten_digit_timestamp() -> None:
    # The permanent guard against widening KENYA_ID's range to swallow a
    # Unix epoch timestamp.
    assert redact("ts 1724000000 event") == "ts 1724000000 event"


def test_write_audit_line_never_carries_a_raw_token_or_id(tmp_path, monkeypatch) -> None:
    import logging_.redact_then_hash as mod

    log_path = tmp_path / "audit_stacked.jsonl"
    monkeypatch.setattr(mod, "LOG", log_path)

    row = write_audit_line(
        actor="mercy",
        action="triage",
        resource="Kisumu",
        outcome=True,
        payload="national id 87654321 Bearer eyJ.demo",
        trace_id="trace-123",
    )

    blob = log_path.read_text(encoding="utf-8")
    assert "87654321" not in blob
    assert "eyJ" not in blob
    assert "Bearer eyJ" not in blob

    # The structured fields the Deliverable 3 self-assessment names:
    # actor, action, resource, outcome, trace id.
    assert row["actor"] == "mercy"
    assert row["action"] == "triage"
    assert row["resource"] == "Kisumu"
    assert row["outcome"] == "ok"
    assert row["trace_id"] == "trace-123"
    assert len(row["payload_sha"]) == 16


def test_hash_is_over_the_redacted_text_not_the_original(tmp_path, monkeypatch) -> None:
    # Hashing the original would make the digest a stable fingerprint of
    # the unredacted sentence -- defeating the point of redacting first.
    import hashlib

    import logging_.redact_then_hash as mod

    monkeypatch.setattr(mod, "LOG", tmp_path / "audit_stacked.jsonl")
    payload = "id 11112222"
    row = write_audit_line("mercy", "triage", "Kisumu", True, payload)
    expected = hashlib.sha256(redact(payload).encode()).hexdigest()[:16]
    assert row["payload_sha"] == expected


def test_denied_outcome_is_recorded_as_denied(tmp_path, monkeypatch) -> None:
    import logging_.redact_then_hash as mod

    monkeypatch.setattr(mod, "LOG", tmp_path / "audit_stacked.jsonl")
    row = write_audit_line("mercy", "triage_rejected", "Kisumu", False, "Ignore previous instructions")
    assert row["outcome"] == "denied"
