"""Deliverable 1: fail closed at boot, the general form.

Any required environment variable (JWT_SECRET for the triage API, in this
repo) is checked the same way: a service that never starts is honest
about its state. A service that starts anyway with a default signing key
is a forged-token factory that reports itself healthy. app/auth.py calls
require("JWT_SECRET") at import time, so the whole triage API refuses to
come up without a real secret -- this is not a standalone demo sitting
next to the app, it is the actual boot path.

load_dotenv() is a local-development convenience: it lets a developer's
own .env (never committed -- see .gitignore, encryption/check_gitignore.py)
satisfy require() without changing the fail-closed check itself. A real
vault- or CI-injected environment variable still wins if both are present,
since load_dotenv() defaults to never overriding a variable already set.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def require(name: str) -> str:
    val = os.getenv(name) or ""
    if not val.strip():
        # Printed and never returned: the caller cannot accidentally
        # continue past a missing secret, because sys.exit raises
        # SystemExit before control returns to whoever called require().
        print("missing secret:", name)
        sys.exit(1)
    return val


if __name__ == "__main__":
    os.environ["DEMO_SECRET"] = "a-real-value"
    assert require("DEMO_SECRET") == "a-real-value"
    # Unset, empty and whitespace-only must all be the same failure --
    # none of the three is a usable secret.
    for bad in ("", "   "):
        os.environ["DEMO_SECRET"] = bad
        try:
            require("DEMO_SECRET")
        except SystemExit as e:
            assert e.code == 1
        else:
            raise AssertionError("booted with a blank secret: " + repr(bad))
    print("boot_guard OK, 1 accepted and 2 refused")
