# AfyaPlus security and Kenya DPA brief

## Risks
- Partner URLs without TLS.
- Secrets committed to git, or baked into a container image.
- Override-style user text trying to hijack the triage model.
- An unpinned FAQ file swapped silently underneath the advisory answers.
- Over-scoped MCP tools -- a single partner credential able to see every
  clinic's stock instead of just its own.
- Audit logs that are themselves a second, unprotected copy of patient data.
- Personal data kept with no retention clock and no deletion evidence.

## Mitigations
- **TLS on every partner-facing endpoint.** `encryption/transit_policy.py`'s
  `transit_ok()` refuses any non-localhost URL that is not `https://`, and
  is unit-tested against a real TLS handshake and against a cleartext
  production host.
- **No secrets in git, and the app will not boot without one.**
  `encryption/secret_refs.yaml` and `encryption/resolve_secrets.py` name the
  signing key and never hold its value; `app/auth.py` calls
  `encryption/boot_guard.py`'s `require("JWT_SECRET")` at import time, so
  the triage API refuses to start without a real secret.
  `encryption/check_gitignore.py` proves `.env` was never tracked, and
  `encryption/kms_twin.json` is the Key Vault / AWS KMS twin card this
  capstone cites in place of a live cloud console.
- **Override-style user text is refused before any model call.**
  `access_control/injection_guard.py` returns a 400-shaped refusal on
  known override phrasing; `app/main.py`'s `/triage` route calls it before
  `triage_model()` ever runs.
- **The MCP surface cannot dump a country.** `logistics_mcp_secure.py`
  requires a `role` on every tool call, checks it against
  `access_control/rbac.py`'s deny-by-default matrix (an unrecognised role
  is refused, not guessed at), and when the caller's role is
  `partner_clinic`, `check_stock` returns exactly one allowlisted clinic's
  row -- never the whole table, and never `clinic_id="*"`. `clinical_ops`
  keeps the cross-clinic routing tools a partner never sees.
  `access_control/mcp_tool_response_fixed.json` versus
  `access_control/mcp_tool_response_leak.json` shows the fixed shape next
  to the over-scoped shape it replaces.
- **JWT authentication is still required.** `/triage` keeps the Week 6
  `Depends(current_user)` + role gate; this week adds authorisation and
  input checks on top, it does not remove authentication.
- **Logs are redacted, then hashed.** `logging_/redact.py` strips Bearer
  tokens, Kenyan phone numbers, M-Pesa codes, and 8-digit national ID
  numbers before anything reaches disk; `logging_/redact_then_hash.py`
  hashes the cleaned text for correlation. `app/main.py` writes one
  structured line per `/triage` call with actor, action, resource,
  outcome, and a trace id -- never a raw Bearer token or identity number.
- **Personal data has a clock, and the clock is evidenced.**
  `dpa/data_inventory.json` names five datasets with a purpose, a
  teaching lawful-basis label, and a retention day count (or an honest
  `null`); `dpa/retention_sweep.py` runs a fixed-clock sweep against
  `dpa/fixtures/old_logs.jsonl` and appends a real row to
  `dpa/deletion_records.jsonl` on every run -- an executable rule, not a
  poster.

## Kenya DPA alignment
- AfyaPlus is the data controller for `/triage`; a cloud model host would
  be a processor; the person the message is about, or the logged-in
  partner user, is the data subject (`dpa/dpa_who.txt`).
- Triage free text is treated as special-category even though the
  product is advisory only (`dpa/data_inventory.json`,
  `dpa/personal_data_inventory_note.md`).
- Every dataset in the inventory carries a purpose, a teaching
  lawful-basis label, and a retention day count or an explicit `null`
  where no clock applies, gated by `dpa/check_inventory.py`.
- An access request is answered with a peppered-hash count, never
  message content (`dpa/rights_lookup.py`).
- The breach drill starts the clock at awareness, contains first, and
  records what changed (`dpa/breach_path.txt`, `dpa/incident_72h_drill.txt`).

## What we will not claim
- No diagnosis, prescription, or dosage advice -- the product is
  advisory only (`governance/poison_vs_injection.md`).
- No claim that this repository has filed with the Office of the Data
  Protection Commissioner, registered under s.18, or obtained a
  lawyer-signed Data Protection Impact Assessment -- `dpa/dpia_stub.md`
  is labelled a teaching stub for exactly this reason, and
  `lawful_basis` fields throughout `dpa/data_inventory.json` are
  explicitly marked `teaching:` rather than a real legal opinion. Legal
  review is pending.
- No claim that residual risk has reached zero -- see
  `dpa/residual_risk.txt` for what is left after each control.
- No claim that this brief satisfies GDPR obligations for any
  EU-resident data subject (`dpa/gdpr_trigger_note.md`).
- No claim that this system cannot be breached. Every control above
  fails closed on a known category of misuse; none of them claims to
  anticipate every category.

On credit or financial decisions specifically (see `benkiyetu_transfer.md`
for the full transfer memo): if any of these controls are ever reused for
a lending or credit-scoring product, a model built this way may only ever
**recommend** a flag to a human reviewer -- it must never **decide** an
approval, a decline, or a price. That line is a governance decision, not
a technical one, and this repository does not make it on anyone's behalf.
