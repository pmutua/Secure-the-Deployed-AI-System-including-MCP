"""Deliverable 1: the Key Vault / KMS twin schema gate.

kms_twin.json is a literacy artefact, not infrastructure-as-code: five
named key-management jobs (store, wrap, rotate, audit, grant identity),
each mapped across Azure and AWS. This is the file the capstone cites
when a live cloud console is unavailable, so the gate exists to stop a
card that documents only one cloud from silently passing.
"""
import json
from pathlib import Path

REQUIRED_JOBS = ["store_secret", "encrypt_dek", "rotate", "audit", "grant_identity"]

# A placeholder is a promise, not a fact. Comparing against this set
# (after normalising) is what stops "TBD" from passing a schema check
# meant to catch exactly that.
PLACEHOLDERS = {"", "tbd", "todo", "n/a"}

DEFAULT_PATH = Path("encryption/kms_twin.json")


def blank(value: object) -> bool:
    return str(value or "").strip().lower() in PLACEHOLDERS


def main(path: Path = DEFAULT_PATH) -> int:
    if not path.exists():
        print("FAIL missing kms_twin.json")
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    problems: list[tuple[str, str]] = []

    for job in REQUIRED_JOBS:
        node = data.get(job)
        if not isinstance(node, dict):
            problems.append((job, "missing job"))
            continue
        for side in ("azure", "aws"):
            if blank(node.get(side)):
                problems.append((job, f"blank {side} twin"))

    if problems:
        print("FAIL kms_twin schema")
        for row in problems:
            print(" ", row)
        return 1

    print("OK kms_twin schema:", len(REQUIRED_JOBS), "jobs, both twins present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
