# test_governance_and_brief.py - supporting evidence: the threat model
# completeness gate, the corpus pin CI gate (and its failure mode), and
# Deliverable 5's heading/overclaim gate against the real manager_brief.md.

from __future__ import annotations

from check_brief import main as check_brief_main
from governance.check_corpus_pin import main as check_corpus_pin_main
from governance.check_threat_model import main as check_threat_model_main
from governance.classify_assets import KIND


def test_threat_model_covers_all_four_asset_kinds() -> None:
    assert check_threat_model_main() == 0


def test_classify_assets_has_all_three_kinds() -> None:
    assert set(KIND.values()) == {"secret", "config", "data"}


def test_corpus_pin_matches_the_committed_knowledge_file() -> None:
    assert check_corpus_pin_main() == 0


def test_corpus_pin_fails_on_a_silent_edit(tmp_path) -> None:
    import json

    from governance.check_corpus_pin import find_mismatches

    tampered = tmp_path / "ors_faq.md"
    tampered.write_text("a silently swapped FAQ with unsafe advice\n")
    fake_pin = {str(tampered): "0" * 64}
    problems = find_mismatches(fake_pin)
    assert problems and "hash mismatch" in problems[0]
    print(json.dumps(problems))  # mirrors pin_fail_notes.txt's transcript


def test_manager_brief_has_the_four_required_headings_and_no_overclaim() -> None:
    assert check_brief_main() == 0


def test_manager_brief_cites_at_least_one_real_filename_per_section() -> None:
    text = open("manager_brief.md", encoding="utf-8").read()
    for must_cite in (
        "encryption/transit_policy.py",
        "access_control/rbac.py",
        "logging_/redact_then_hash.py",
        "dpa/retention_sweep.py",
    ):
        assert must_cite in text, f"manager_brief.md never cites {must_cite}"
