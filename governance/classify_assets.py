"""Governance evidence: tell a secret apart from config and from data.

Each asset AfyaPlus holds fails differently when it leaks, so each one
needs its own recovery path:
  - secret  -> rotate it (JWT_SECRET, OPENAI_API_KEY)
  - config  -> review the diff (a prompt/FAQ file is versioned, not vaulted)
  - data    -> a Kenya DPA incident path (chat logs, clinic records)
"""

KIND = {
    "JWT_SECRET": "secret",
    "SUBJECT_PEPPER": "secret",
    "OPENAI_API_KEY": "secret",
    # A knowledge file is versioned config, not a credential -- see
    # governance/knowledge/pin.json. This is the line that decides
    # whether an asset goes in a vault or in a pull request.
    "governance/knowledge/ors_faq.md": "config",
    "triage_messages.json": "data",
    "clinics.json": "data",
}


if __name__ == "__main__":
    assert KIND["JWT_SECRET"] == "secret"
    assert KIND["triage_messages.json"] == "data"
    assert KIND["governance/knowledge/ors_faq.md"] == "config"
    assert set(KIND.values()) == {"secret", "config", "data"}
    print("classify_assets OK", len(KIND), "assets,", len(set(KIND.values())), "kinds")
