# Week 9: AI Security and Compliance

## Overview
This repository locks the AfyaPlus triage API (`app/`, reused from Week 6)
and the logistics MCP server (`logistics_mcp_secure.py`, reused from
Weeks 6/8) with encryption, access control, structured logging, and
Kenya Data Protection Act alignment. It aligns to Kenya's Data Protection
Act, 2019, with every `lawful_basis` label explicitly marked `teaching:`
rather than a real legal opinion (`dpa/dpia_stub.md`: "legal review
pending"). The manager brief lives at [`manager_brief.md`](manager_brief.md),
with the transfer-to-a-lender variant at
[`benkiyetu_transfer.md`](benkiyetu_transfer.md). All 75 tests in
`tests/` pass offline, at $0 additional spend -- every model call this
week is stubbed, per the capstone's own cost budget.

Scope decision: the Week 6 LangChain agent that calls the MCP server
live (`agent_service.py`) is out of scope this week. The MCP server is
tested directly, tool-by-tool, which is the capstone's own stated
fallback for "No live MCP server." Nothing about this decision weakens
the access-control evidence below -- `tests/test_mcp_tools.py` calls the
real tool functions in `logistics_mcp_secure.py` directly, not a stub.

## Encryption
- **transit_ok / TLS evidence:** `encryption/transit_policy.py`.
  `evidence/transit_policy.log` (unit assertions, incl. a cleartext
  production host refused) and `evidence/curl_transcript.log` (every
  real response from the live API, over this lab's localhost HTTP
  exception).
- **gitignore / resolve_secrets:** `encryption/check_gitignore.py`,
  `encryption/secrets_not_in_git.sh`, `encryption/resolve_secrets.py`,
  `encryption/boot_guard.py`. `evidence/check_gitignore.log`,
  `evidence/secrets_not_in_git.log`, and
  `evidence/boot_fail_missing_secret.log` -- the last one captures both
  `resolve_secrets.py`'s and the **real app's own import-time boot
  check** (`app/auth.py` calls `boot_guard.require("JWT_SECRET")`)
  refusing to start without a secret (exit 1), then succeeding once one
  is set.
- **Key Vault or KMS, or the fallback twin JSON:** no Azure subscription
  or AWS account this week (see "Fallbacks declared"). `encryption/secret_refs.yaml`
  names the vault objects without ever holding a value;
  `encryption/kms_twin.json` + `encryption/check_kms_twin.py` is the
  Azure/AWS twin card (`evidence/check_kms_twin.log`). At-rest sketch:
  `encryption/encrypt_at_rest.py` (`evidence/encrypt_at_rest.log`).
  Compose references `${JWT_SECRET}`, never a value:
  [`docker-compose.yml`](docker-compose.yml).

## Access control (including MCP)
- **rbac.py roles:** `access_control/rbac.py` -- `partner_clinic` and
  `clinical_ops`, deny-by-default for any other role
  (`evidence/rbac.log`, `tests/test_access_control.py`).
- **injection_guard:** `access_control/injection_guard.py`, wired into
  `app/main.py`'s `/triage` route *before* `triage_model()` runs
  (`evidence/injection_guard.log`, `evidence/curl_transcript.log`'s last
  call, `evidence/redact_then_hash.log`'s `triage_rejected` rows).
- **clinic allowlist:** `access_control/clinics_allowlist.json` +
  `access_control/allowlist_stock.py` (standalone worked example,
  `evidence/allowlist_stock.log`), wired into the real
  `logistics_mcp_secure.py`'s `check_stock` for the `partner_clinic`
  role. `evidence/mcp_cannot_dump_a_country.log` is the direct answer to
  the brief's own test: a `partner_clinic` credential gets exactly one
  clinic's row; `clinic_id="*"` and a real-but-unauthorised clinic id are
  both refused with the same 400 shape; an unrecognised role gets 403,
  never a stack trace, never an environment dump
  (`access_control/mcp_tool_response_fixed.json` vs.
  `access_control/mcp_tool_response_leak.json` shows the shape this
  replaces). `tests/test_mcp_tools.py` exercises all of this against the
  real tool functions.
- JWT is still required on `/triage`, unchanged in shape from Week 6
  (`app/auth.py`'s `current_user` + `require_role("coordinator")`) --
  `evidence/curl_transcript.log`'s 401 -> 403 -> 200 ladder.

## Logging
- **Path to the jsonl:** `logging_/logs/audit_stacked.jsonl` (gitignored
  runtime output; a captured snapshot is `evidence/redact_then_hash.log`).
- **Redact and hash approach:** `logging_/redact.py` (strips Bearer
  tokens, Kenyan phone numbers, M-Pesa codes, 8-digit national IDs) then
  `logging_/redact_then_hash.py` (hashes the *cleaned* text, never the
  original), called from `app/main.py` on every `/triage` call --
  accepted or refused -- with actor, action, resource, outcome, and a
  trace id. `evidence/redact.log`, `evidence/redact_then_hash.log`
  (includes real lines written by the live API during
  `tests/test_api.py`, with no raw token or identity number in any of
  them).

## Kenya DPA
- **Inventory path:** `dpa/data_inventory.json`, gated by
  `dpa/check_inventory.py` (`evidence/check_inventory.log`). Five
  datasets; `triage_messages` flagged `special_category: true`.
- **Retention:** `dpa/retention.json` plus the executable sweep,
  `dpa/retention_sweep.py`, run against a frozen clock
  (`evidence/retention_sweep.log`), appending to the append-only
  `dpa/deletion_records.jsonl` on every run -- never itself swept.
- **Rights stub / owner:** `dpa/rights_lookup.py` answers an access
  request with a peppered-hash count, never message content
  (`evidence/rights_lookup.log`, including the fail-closed case with no
  pepper set); access/erasure owner named in `dpa/dpa_who.txt` and
  `dpa/dpa_extra_duties.md`.

## Manager brief
Link: [`manager_brief.md`](manager_brief.md). Four headings confirmed:
Risks, Mitigations, Kenya DPA alignment, What we will not claim
(`evidence/check_brief.log`, `check_brief.py`). The word "unhackable"
does not appear anywhere in this repository. A finance-transfer
paragraph (recommend, not decide, on credit) closes the brief and is
expanded in [`benkiyetu_transfer.md`](benkiyetu_transfer.md).

## Fallbacks declared
- [x] no Azure Key Vault (local-env plus `encryption/kms_twin.json`)
- [x] no AWS account (same twin card; the AWS column is never skipped)
- [x] local MCP stub (`logistics_mcp_secure.py` run and tested directly,
  stdio-ready; no live LangChain agent call this week -- see "Overview")
- [x] no lawyer or data protection officer (`dpa/dpia_stub.md`'s
  `lawful_basis` fields are all labelled `teaching:`; "legal review
  pending")
- [x] no paid model access (`app/triage_model.py` is a deterministic
  stub; the injection guard and the corpus pin are never tested against
  a live model call)
- [x] no production domain (`encryption/transit_policy.py`'s
  `transit_ok()` still refuses `http://afyaplus-prod.ke/triage` with no
  network access, see `tests/test_encryption.py`)

## Ties to Weeks 6-8
- `app/auth.py`, `app/rate_limit.py`, `app/models.py`: Week 6's JWT +
  role-gate + rate-limit triage service, unchanged in shape except that
  `auth.py` now resolves `JWT_SECRET` through `encryption/boot_guard.py`
  instead of a dev-only fallback default.
- `app/main.py`: Week 6's `/health`, `/token`, `/triage` routes, with
  this week's injection guard and redact-then-hash audit logging wired
  into the real `/triage` request path.
- `logistics_mcp_secure.py`: Weeks 6/8's `logistics_mcp.py` /
  `logistics_mcp_versioned.py` four-tool FastMCP server, with every tool
  now taking an explicit `role` argument checked against
  `access_control/rbac.py`, and `check_stock` additionally scoped to the
  caller's own allowlisted clinic when that role is `partner_clinic`.
  `clinics.json` carries the same three partner clinics as Weeks 6/8
  plus two more (Kisii, Kisumu West) that exist in the system but are
  deliberately outside this partner's allowlist, so the "cannot dump a
  country" claim has something real to refuse.
- `docker-compose.yml` / `Dockerfile`: Week 6's container pattern,
  referencing `${JWT_SECRET}` rather than a value.

## Checklist
- [x] Secrets not in git -- `evidence/check_gitignore.log`,
  `evidence/secrets_not_in_git.log`
- [x] MCP cannot dump the environment or every clinic --
  `evidence/mcp_cannot_dump_a_country.log`
- [x] The brief is readable by a non-engineer --
  [`manager_brief.md`](manager_brief.md) uses no YAML and no jargon a
  manager would need to look up
