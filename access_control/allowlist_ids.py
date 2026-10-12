"""Deliverable 2: allowlists for structured fields.

Allowlists beat blocklists whenever a field is structured (clinic_id,
item, partner_id): the valid values can be enumerated, so anything else
is refused without argument. Free text (the triage message body) cannot
be enumerated, which is why it gets injection_guard.py and a length cap
instead of this pattern.
"""

KNOWN_CLINICS = {"KSM-01", "VIH-01", "HBA-01"}


def clinic_or_400(clinic_id: str) -> str:
    """Normalise first, decide second -- never the other way round.

    Deciding on the raw value first would make the allowlist
    case-sensitive and whitespace-sensitive, which is trivially defeated
    by a client sending " ksm-01 " instead of "KSM-01".
    """
    cid = clinic_id.strip().upper()
    if cid not in KNOWN_CLINICS:
        raise ValueError("unknown clinic_id")
    return cid


if __name__ == "__main__":
    assert clinic_or_400(" ksm-01 ") == "KSM-01"  # normalise, then decide
    assert clinic_or_400("VIH-01") == "VIH-01"
    for bad in ("KSM-99", "", "KSM-01; DROP TABLE"):
        try:
            clinic_or_400(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("allowlist let through: " + repr(bad))
    print("allowlist_ids OK", len(KNOWN_CLINICS), "clinics, 3 refusals")
