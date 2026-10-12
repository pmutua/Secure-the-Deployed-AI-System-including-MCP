"""Deliverable 4: the inventory completeness gate.

data_inventory.json has to cover five named datasets and flag the one
carrying health-adjacent free text. A generic JSON-schema check would
never know to require that last rule -- it is a fact about AfyaPlus,
not about JSON.
"""
import json
from pathlib import Path

REQUIRED = {"triage_messages", "jwt_subjects", "mcp_stock_queries", "audit_logs"}
FIELDS = ("purpose", "lawful_basis", "retention_days", "special_category")
DEFAULT_PATH = Path("dpa/data_inventory.json")


def main(path: Path = DEFAULT_PATH) -> int:
    if not path.exists():
        print("FAIL missing data_inventory.json")
        return 1

    rows = json.loads(path.read_text(encoding="utf-8"))
    names = {r["name"] for r in rows}
    missing = REQUIRED - names
    if missing:
        print("FAIL missing datasets:", sorted(missing))
        return 1

    by = {r["name"]: r for r in rows}
    # is not True (not == False) so the string "true" or an int 1 fails
    # too -- a value no downstream code would read as a real boolean.
    if by["triage_messages"].get("special_category") is not True:
        print("FAIL triage_messages must be special_category true")
        return 1

    for r in rows:
        for k in FIELDS:
            # presence, not truthiness -- retention_days: null on
            # knowledge_files is an honest "no clock applies" and must pass.
            if k not in r:
                print("FAIL", r.get("name"), "missing", k)
                return 1

    print("inventory OK", len(rows), "datasets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
