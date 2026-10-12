"""Deliverable 1: what encryption at rest means on a laptop.

In a managed platform you do not hand-roll AES inside a FastAPI route --
you enable the provider's encryption flags and keep the customer master
key in Key Vault or KMS (encryption/kms_twin.json, encryption/secret_refs.yaml).
This file is the local sketch that makes the deliverable buildable with
no cloud account: it proves the *shape* of at-rest encryption (a key
that lives outside the blob it protects) without asking anyone to design
a cipher.

Fernet (from the `cryptography` package) is a recipe, not a raw cipher:
AES in CBC mode plus an HMAC plus a timestamp, bundled so nobody has to
choose a mode, a padding scheme, or a nonce by hand.
"""
import os
from pathlib import Path

from cryptography.fernet import Fernet


def load_key() -> bytes:
    """Read the Fernet key from the environment; fail closed if absent.

    Raising SystemExit rather than falling back to a hard-coded default
    is the point: a default key baked into the script would make the
    "encryption" decorative, since anyone reading the source would also
    hold the key.
    """
    raw = os.getenv("LOCAL_FERNET_KEY")
    if not raw:
        raise SystemExit("missing LOCAL_FERNET_KEY (generate with Fernet.generate_key())")
    return raw.encode() if isinstance(raw, str) else raw


def encrypt_blob(plain: bytes, out: Path) -> None:
    token = Fernet(load_key()).encrypt(plain)
    # write_bytes, not write_text: a Fernet token is base64 bytes, and a
    # text write would depend on the platform's default encoding.
    out.write_bytes(token)


def decrypt_blob(path: Path) -> bytes:
    """Round-trip check only -- the only proof the pair actually inverts."""
    return Fernet(load_key()).decrypt(path.read_bytes())


if __name__ == "__main__":
    # Scoped under encryption/secrets/ and gitignored -- this is a
    # generated demo artefact, not source content.
    Path("encryption/secrets").mkdir(parents=True, exist_ok=True)
    if not os.getenv("LOCAL_FERNET_KEY"):
        key = Fernet.generate_key().decode()
        print("export LOCAL_FERNET_KEY=" + key)
        os.environ["LOCAL_FERNET_KEY"] = key
    blob_path = Path("encryption/secrets/jwt.enc")
    encrypt_blob(b"jwt-demo-value", blob_path)
    assert decrypt_blob(blob_path) == b"jwt-demo-value"
    print("encrypt_at_rest OK")
