# Impact assessment stub (teaching)

## System
AfyaPlus triage plus the logistics MCP server

## Risks
- Advisory urgency bands could be misread by an out-of-network user as a
  diagnosis, delaying real care.
- Health-adjacent free text stored longer than needed increases exposure
  if a log store is ever breached.
- A wrong or stale pinned FAQ could surface an unsafe next-step
  suggestion.
- Over-scoped MCP tool access could let one credential enumerate every
  clinic's stock instead of just its own.

## Mitigations
- Advisory-only language enforced throughout the product
  (`governance/poison_vs_injection.md`).
- A 90-day clock on `triage_messages` with a real deletion record
  (`dpa/retention_sweep.py`, `dpa/deletion_records.jsonl`).
- The corpus hash pinned and checked in CI
  (`governance/knowledge/pin.json`, `governance/check_corpus_pin.py`).
- A per-clinic allowlist plus role-scoped MCP tools
  (`logistics_mcp_secure.py`, `access_control/rbac.py`).

## Residual
- A confident, wrong urgency band can still be issued; the mitigation is
  human clinic-staff review, not model certainty.
- Deletion removes primary storage rows; a full accounting of every
  backup copy sharing the same clock is not yet built.

Label: teaching stub, not a lawyer-signed assessment. "legal review
pending" -- see README's fallbacks.
