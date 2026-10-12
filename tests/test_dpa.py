# test_dpa.py - Deliverable 4 evidence: inventory completeness, a
# fixed-clock retention sweep with a real deletion record, and a
# data-subject rights lookup that answers with a count, never content.

from __future__ import annotations

import json

from dpa.check_inventory import main as check_inventory_main
from dpa.retention_sweep import CUT, DELETION_LOG, NOW, sweep
from dpa.rights_lookup import lookup


def test_inventory_covers_all_required_datasets() -> None:
    assert check_inventory_main() == 0


def test_inventory_marks_triage_messages_special_category() -> None:
    rows = json.loads(open("dpa/data_inventory.json", encoding="utf-8").read())
    by_name = {r["name"]: r for r in rows}
    assert by_name["triage_messages"]["special_category"] is True


def test_knowledge_files_retention_is_an_honest_null() -> None:
    rows = json.loads(open("dpa/data_inventory.json", encoding="utf-8").read())
    by_name = {r["name"]: r for r in rows}
    assert by_name["knowledge_files"]["retention_days"] is None


def test_retention_sweep_drops_old_rows_and_keeps_fresh_ones(tmp_path) -> None:
    src = tmp_path / "old_logs.jsonl"
    dest = tmp_path / "kept.jsonl"
    src.write_text(
        json.dumps({"ts": CUT - 10, "id": "old"}) + "\n"
        + json.dumps({"ts": NOW - 100, "id": "fresh"}) + "\n",
        encoding="utf-8",
    )
    report = sweep(src=src, dest=dest, dataset="triage_messages")
    assert report["count_dropped"] == 1
    assert report["count_kept"] == 1
    assert dest.read_text(encoding="utf-8").count("fresh") == 1


def test_retention_sweep_appends_a_deletion_record_evidence_is_never_swept(monkeypatch, tmp_path) -> None:
    import dpa.retention_sweep as mod

    fake_deletion_log = tmp_path / "deletion_records.jsonl"
    monkeypatch.setattr(mod, "DELETION_LOG", fake_deletion_log)
    monkeypatch.setattr(mod, "SWEEP_REPORT_PATH", tmp_path / "sweep_report.json")

    src = tmp_path / "old_logs.jsonl"
    src.write_text(json.dumps({"ts": 0, "id": "ancient"}) + "\n", encoding="utf-8")
    mod.sweep(src=src, dest=tmp_path / "kept.jsonl")
    mod.sweep(src=src, dest=tmp_path / "kept.jsonl")

    lines = fake_deletion_log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2  # append-only: two runs, two records, nothing overwritten


def test_real_deletion_records_file_has_at_least_one_captured_run() -> None:
    # The committed evidence file, not a tmp_path copy -- proves the
    # sweep has actually been run at least once in this repository.
    assert DELETION_LOG.exists()
    lines = [line for line in DELETION_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 1
    row = json.loads(lines[-1])
    assert row["dataset"] == "triage_messages"
    assert "cut_ts" in row["range"]


def test_rights_lookup_answers_with_count_not_content() -> None:
    result = lookup("KSM-01")
    assert result["found"] is True
    assert isinstance(result["n_events"], int)


def test_rights_lookup_clinic_with_no_rows_is_not_found() -> None:
    result = lookup("HBA-01")
    assert result == {"found": False, "n_events": 0}


def test_rights_lookup_fails_closed_without_a_pepper(monkeypatch) -> None:
    import pytest

    from dpa import rights_lookup

    monkeypatch.delenv("SUBJECT_PEPPER", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(SystemExit):
        rights_lookup.pepper()
