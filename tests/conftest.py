# conftest.py - sets the environment variables a real deployment would
# inject via a vault or CI secret store, so the test suite exercises the
# fail-closed boot path (encryption/boot_guard.py) the same way
# production does, without needing a committed .env. setdefault means a
# developer's own .env (never committed) or shell export still wins if
# already present. This file runs before any test module in this
# directory imports app.main -- which is what lets app.auth's
# import-time require("JWT_SECRET") succeed during collection.
import os

os.environ.setdefault("JWT_SECRET", "test-only-secret-for-pytest-32chars!")
os.environ.setdefault("SUBJECT_PEPPER", "lab-demo-pepper-not-a-real-secret-2026")
# A fixed, test-only Fernet key -- not a production secret, just enough
# entropy for encrypt_at_rest.py's round-trip check to be deterministic.
os.environ.setdefault("LOCAL_FERNET_KEY", "C0unOhWVT5pQSaflTwS9fd6eOl4loLs80pGjP1jqF0E=")
