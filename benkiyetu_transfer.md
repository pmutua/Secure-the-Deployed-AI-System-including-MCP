# Memo: AfyaPlus controls, transferred to BenkiYetu (a hypothetical lender)

## Copy
1. TLS/HTTPS on every partner-facing endpoint (`encryption/transit_policy.py`)
   -- the mechanism is identical whether the payload is a triage message or a
   loan question.
2. Secrets kept as vault references, never values, in git
   (`encryption/secret_refs.yaml`, `encryption/resolve_secrets.py`) -- a
   signing key or a bureau API key fails closed the same way.
3. Role-scoped tool access (`access_control/rbac.py`) -- swap
   `partner_clinic`/`clinical_ops` for `agent`/`credit_ops`/`auditor` and the
   deny-by-default matrix needs no other change.
4. Redacted, hashed audit logs (`logging_/redact.py`,
   `logging_/redact_then_hash.py`) -- a phone number or an 8-digit identity
   number is exactly as sensitive in a wallet app as in a clinic chat.

## Must change
Credit decisions. The AfyaPlus pattern lets a model suggest an urgency band
that a clinician can act on or ignore. A fraud-hint model at BenkiYetu may
only ever flag a case for a human `credit_ops` reviewer -- it must never be
the system that approves, declines, or prices a loan. The moment a model's
JSON output becomes the credit action instead of a suggestion routed to a
person, the governance failure is not a bug in the model; it is a decision
AfyaPlus never had to make, and this repository does not make it for
BenkiYetu either -- that line stays with their own compliance function.

## Will not copy
- AfyaPlus's 90-day `triage_messages` retention clock, unmodified: Credit
  Reference Bureau regulations set retention for credit data in years, not
  days, so BenkiYetu's own retention table needs a bureau-driven number,
  and an erasure request against a bureau record has to be documented as a
  conflict and routed to the record's owner -- never silently honoured by
  an FAQ assistant.
- The assumption that "advisory language" alone satisfies the statute: a
  wrong fee-schedule answer is a mis-selling risk reviewed by compliance,
  not a safety risk reviewed by a clinician, so the review owner changes
  even though the pinned-corpus mechanism (`governance/corpus_pin.py`)
  does not.

This memo exists to show the controls generalise, not to imply BenkiYetu is
a real client or that this capstone has done BenkiYetu's compliance work.
