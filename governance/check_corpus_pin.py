"""Governance evidence: the corpus pin CI gate.

Re-hashes every file listed in knowledge/pin.json and exits 1 on any
mismatch or missing file. A silent FAQ edit must fail this exactly the
way a prompt edit fails a prompt-pin check.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

DEFAULT_PIN_PATH = Path("governance/knowledge/pin.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pin(pin_path: Path = DEFAULT_PIN_PATH) -> dict[str, str]:
    return json.loads(pin_path.read_text(encoding="utf-8"))


def find_mismatches(pin: dict[str, str]) -> list[str]:
    problems: list[str] = []
    for rel_path, expected_sha in pin.items():
        path = Path(rel_path)
        if not path.exists():
            problems.append(f"{rel_path}: file is missing")
            continue
        actual = sha(path)
        if actual != expected_sha:
            problems.append(
                f"{rel_path}: hash mismatch (pinned {expected_sha[:12]}..., got {actual[:12]}...)"
            )
    return problems


def main(pin_path: Path = DEFAULT_PIN_PATH) -> int:
    pin = load_pin(pin_path)
    problems = find_mismatches(pin)
    if problems:
        print("FAIL: corpus pin mismatch")
        for problem in problems:
            print(" -", problem)
        return 1
    print("OK", len(pin), "knowledge file(s) match the pin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
