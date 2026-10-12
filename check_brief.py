"""Deliverable 5: the manager brief heading and overclaim gate.

Checks the real manager_brief.md directly -- this is a deliverable
grading gate, not a warm-up exercise, so it should fail loudly on the
document a marker will actually read. The banned-word check runs before
the heading check, so a well-structured brief that overclaims still
fails on the finding that matters most.
"""
import sys
from pathlib import Path

HEADS = ["Risks", "Mitigations", "Kenya DPA alignment", "What we will not claim"]
BANNED = ["unhackable"]
DEFAULT_PATH = Path("manager_brief.md")


def main(path: str | Path = DEFAULT_PATH) -> int:
    text = Path(path).read_text(encoding="utf-8")
    low = text.lower()

    for word in BANNED:
        if word in low:
            print(f"FAIL: do not claim {word}")
            return 1

    missing = [h for h in HEADS if h.lower() not in low]
    if missing:
        print("FAIL missing headings", missing)
        return 1

    print("brief headings OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:2]))
