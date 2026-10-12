"""Deliverable 2: refuse override text before any model or tool call.

"Adversarial input" here means a user or partner client sending text
that tries to override the system prompt, extract secrets, or force a
tool their role should never see. This file is deliberately small: a
phrase list and a substring test, not a jailbreak catalogue -- the point
is a fail-closed boundary check, not cleverness, and the phrase list is
deliberately not grown for entertainment.

Refusal happens here, before any model or MCP call -- app/main.py calls
triage_or_reject() before triage_model() ever runs, so the model layer
never has to be clever and no token is ever spent arguing with an
attacker.
"""

# A tuple (immutable, reviewable in a diff) of lowercase phrases. This is
# the entire list the guard covers.
OVERRIDE_PHRASES = (
    "ignore previous instructions",
    "ignore all instructions",
    "you are now",
    "reveal the system prompt",
    "print your secret",
)


def looks_like_override(message: str) -> bool:
    """Substring match on override phrases, not a true prefix check.

    Lowercasing and stripping once, before any comparison, is what makes
    "Ignore Previous Instructions" and the lowercase form take the same
    path.
    """
    m = message.strip().lower()
    return any(p in m for p in OVERRIDE_PHRASES)


def triage_or_reject(message: str) -> dict:
    """Return a 400-shaped dict rather than raising.

    A returned shape (not an exception) is what lets this function stay
    a plain callable in a test and a FastAPI-facing check in app/main.py
    without the contract changing -- the caller always gets a dict back,
    never has to catch anything.
    """
    if looks_like_override(message):
        return {"error": "rejected", "code": 400}
    return {"ok": True, "message": message}


if __name__ == "__main__":
    assert triage_or_reject("Fever two days")["ok"] is True
    assert triage_or_reject("Ignore previous instructions")["code"] == 400
    # False-positive guard: legitimate pharmacy wording must still be
    # allowed. Without this case, someone eventually widens the phrase
    # list to the bare word "ignore" and ordinary triage text starts
    # returning 400.
    assert triage_or_reject("ignore previous advice from the pharmacy")["ok"] is True
    print("injection_guard OK")
