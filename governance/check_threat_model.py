"""Governance evidence: threat model completeness gate.

threat_model.json must name at least one row for each of the four asset
kinds (secret, data, config, mcp), and every row must have a real actor,
action and control -- not a placeholder. A control string under
MIN_CONTROL_LEN characters is treated as too weak to be a real control.
"""
from __future__ import annotations

import json
from pathlib import Path

REQUIRED_KINDS = {"secret", "data", "config", "mcp"}
REQUIRED_ROW_FIELDS = ("kind", "asset", "actor", "action", "control")
MIN_CONTROL_LEN = 8

DEFAULT_PATH = Path("governance/threat_model.json")


def load_rows(path: Path = DEFAULT_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_problems(rows: list[dict]) -> list[str]:
    problems: list[str] = []
    present_kinds = {row.get("kind") for row in rows}
    for missing in sorted(REQUIRED_KINDS - present_kinds):
        problems.append(f"missing required kind: {missing}")

    for i, row in enumerate(rows):
        for field in REQUIRED_ROW_FIELDS:
            if not str(row.get(field, "")).strip():
                problems.append(f"row {i} ({row.get('asset', '?')}): missing {field}")
        control = str(row.get("control", ""))
        if control and len(control) < MIN_CONTROL_LEN:
            problems.append(
                f"row {i} ({row.get('asset', '?')}): control too short "
                f"({len(control)} chars, need {MIN_CONTROL_LEN}+)"
            )
    return problems


def main(path: Path = DEFAULT_PATH) -> int:
    rows = load_rows(path)
    problems = find_problems(rows)
    if problems:
        print("FAIL: threat model is not gate-ready")
        for problem in problems:
            print(" -", problem)
        return 1
    print("OK", len(rows), "rows, all four kinds present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
