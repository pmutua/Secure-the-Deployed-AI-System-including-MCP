"""Deliverable 1: fail closed when a vault-referenced secret is absent.

Reads secret_refs.yaml, looks up the environment variable each vault
object is supposed to arrive as, and refuses to report success when that
value is missing, empty, or whitespace-only. This is the Azure Key
Vault / AWS KMS fallback the capstone brief names explicitly: "No Azure
Key Vault: submit secret_refs.yaml plus resolve_secrets.py using
environment injection, and cite kms_twin.json."

load_dotenv() is a local-development convenience, not part of the
resolver's contract: the environment variable is where a real vault or
CI injects the secret at runtime; a developer's own .env (never
committed) is just one more legitimate way for that variable to already
be set before resolve() runs.
"""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

DEFAULT_REFS_PATH = Path("encryption/secret_refs.yaml")


def load_ref(key: str, refs_path: Path = DEFAULT_REFS_PATH) -> dict:
    # yaml.safe_load refuses to construct arbitrary Python objects from
    # the file -- a config file is exactly the kind of input an attacker
    # would like to see loaded unsafely.
    refs = yaml.safe_load(refs_path.read_text(encoding="utf-8"))
    return refs[key]


def resolve(key: str = "jwt_secret", refs_path: Path = DEFAULT_REFS_PATH) -> int:
    ref = load_ref(key, refs_path)
    # The env var name is read from the YAML (with a sensible default)
    # rather than hard-coded, so renaming the vault object is a config
    # edit, not a code change.
    env_key = ref.get("env", "JWT_SECRET")

    # os.getenv(...) or "" then .strip() collapses three distinct failure
    # modes -- unset, empty, whitespace-only -- into one: none of the
    # three is a usable signing key.
    val = os.getenv(env_key) or ""
    if not val.strip():
        print("missing secret:", ref["name"])
        return 1

    # Print the name and the length only. A resolver that echoes the
    # value to prove it loaded has just written the secret into every CI
    # log that ever runs it.
    print(f"loaded: {ref['name']} (len={len(val)})")
    return 0


def main() -> int:
    return resolve("jwt_secret")


if __name__ == "__main__":
    raise SystemExit(main())
