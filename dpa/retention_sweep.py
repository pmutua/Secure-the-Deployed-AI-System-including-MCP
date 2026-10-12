"""Deliverable 4: apply a fixed-clock retention rule and record the deletion.

NOW is a frozen integer, not time.time(), so the same fixture always
produces the same counts -- a failing assertion means a code change, not
the passage of a calendar day. deletion_records.jsonl is only ever
appended to and is never itself swept: it is the evidence a controller
would have to produce that a deletion actually happened.
"""
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

# A frozen "current time" (Unix seconds), NOT datetime.now()/time.time()
# -- this is what makes every run of this script produce identical
# results, essential for a reliable demo/test.
NOW = 1_724_000_000

KEEP_SECONDS = 90 * 24 * 3600
CUT = NOW - KEEP_SECONDS

FIXTURE_PATH = Path("dpa/fixtures/old_logs.jsonl")
KEPT_PATH = Path("dpa/kept.jsonl")
DELETION_LOG = Path("dpa/deletion_records.jsonl")
SWEEP_REPORT_PATH = Path("dpa/sweep_report.json")


def sweep(
    src: Path = FIXTURE_PATH,
    dest: Path = KEPT_PATH,
    dataset: str = "triage_messages",
) -> dict:
    """Drop rows older than the retention cutoff and record what happened."""
    kept, dropped = [], []

    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        # >= puts a row exactly on the boundary in the kept set -- a
        # decision made and documented, not left for a reviewer to guess.
        (kept if row["ts"] >= CUT else dropped).append(row)

    dest.write_text("".join(json.dumps(r) + "\n" for r in kept), encoding="utf-8")

    report = {
        "job_id": str(uuid.uuid4()),
        "run_date": datetime.fromtimestamp(NOW, UTC).date().isoformat(),
        "clock": "fixture: frozen NOW, not a production run",
        "dataset": dataset,
        "range": {"cut_ts": CUT, "now_ts": NOW},
        "count_dropped": len(dropped),
        "count_kept": len(kept),
        "rule": f"{KEEP_SECONDS // 86400}-day retention for {dataset}",
    }

    # Append-only. A sweeper that deletes its own evidence has removed
    # the only proof the rule was ever applied.
    with DELETION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report) + "\n")

    SWEEP_REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> dict:
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FIXTURE_PATH.exists():
        FIXTURE_PATH.write_text(
            json.dumps({"ts": NOW - KEEP_SECONDS - 10, "id": "old"}) + "\n"
            + json.dumps({"ts": NOW - 100, "id": "fresh"}) + "\n",
            encoding="utf-8",
        )
    report = sweep()
    print(report)
    return report


if __name__ == "__main__":
    main()
