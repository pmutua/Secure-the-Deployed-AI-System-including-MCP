# test_encryption.py - Deliverable 1 evidence, run offline. Real-network
# calls (tls_handshake_ok, https_get_ok) are exercised against a fake
# socket/urlopen rather than depending on a live endpoint being
# reachable during CI.

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from encryption import boot_guard, check_gitignore, encrypt_at_rest, transit_policy
from encryption.check_kms_twin import main as check_kms_twin_main


def test_transit_ok_requires_https_for_non_localhost() -> None:
    assert transit_policy.transit_ok("https://api.afyaplus.ke/triage") is True
    assert transit_policy.transit_ok("http://api.afyaplus.ke/triage") is False


def test_transit_ok_refuses_a_cleartext_production_host() -> None:
    # The "No production domain" fallback: this must pass with zero
    # network access, since afyaplus-prod.ke resolves nowhere real.
    assert transit_policy.transit_ok("http://afyaplus-prod.ke/triage") is False


def test_transit_ok_allows_localhost_http_as_a_documented_lab_exception() -> None:
    assert transit_policy.transit_ok("http://127.0.0.1:8000/triage") is True
    assert transit_policy.transit_ok("http://localhost:8000/triage") is True


def test_transit_ok_fails_closed_on_unparseable_url() -> None:
    assert transit_policy.transit_ok("not-a-url-at-all") is False


def test_tls_handshake_ok_fails_closed_on_any_error(monkeypatch) -> None:
    def _boom(host, port=443, timeout=5.0):
        raise OSError("no network in CI")

    monkeypatch.setattr(transit_policy.ssl, "get_server_certificate", _boom)
    assert transit_policy.tls_handshake_ok("api.afyaplus.ke") is False


def test_https_get_ok_checks_policy_before_the_network(monkeypatch) -> None:
    # A cleartext URL must never reach urlopen at all.
    called = {"hit": False}

    def _should_not_run(*args, **kwargs):
        called["hit"] = True
        raise AssertionError("urlopen should never be called for a cleartext URL")

    monkeypatch.setattr(transit_policy.urllib.request, "urlopen", _should_not_run)
    assert transit_policy.https_get_ok("http://api.afyaplus.ke/triage") is False
    assert called["hit"] is False


def test_env_is_gitignored() -> None:
    # This repo's own .gitignore lists .env; check_gitignore.py proves it
    # with git's own check-ignore, not a string search.
    assert check_gitignore.env_is_gitignored(os_cwd()) is True


def test_check_gitignore_main_passes_on_this_repo() -> None:
    assert check_gitignore.main(os_cwd()) == 0


def os_cwd():
    from pathlib import Path

    return Path(__file__).resolve().parent.parent


def test_boot_guard_accepts_a_real_value() -> None:
    os.environ["DEMO_SECRET_FOR_TEST"] = "a-real-value"
    assert boot_guard.require("DEMO_SECRET_FOR_TEST") == "a-real-value"


def test_boot_guard_fails_closed_on_missing_or_blank_secret() -> None:
    for bad in ("", "   "):
        os.environ["DEMO_SECRET_FOR_TEST"] = bad
        with pytest.raises(SystemExit) as exc_info:
            boot_guard.require("DEMO_SECRET_FOR_TEST")
        assert exc_info.value.code == 1


def test_boot_guard_cli_exits_1_when_secret_truly_unset() -> None:
    # A real subprocess, with the variable removed from the child's
    # environment entirely -- the captured-run evidence the Deliverable
    # 1 self-assessment asks for ("a missing-secret exit 1").
    env = {k: v for k, v in os.environ.items() if k != "JWT_SECRET"}
    result = subprocess.run(
        [sys.executable, "-c", "import os; os.environ.pop('JWT_SECRET', None); "
         "import sys; sys.path.insert(0, '.'); from encryption.boot_guard import require; require('JWT_SECRET')"],
        cwd=os_cwd(),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "missing secret" in result.stdout


def test_resolve_secrets_reports_missing_when_env_unset(monkeypatch) -> None:
    from encryption import resolve_secrets

    monkeypatch.delenv("JWT_SECRET", raising=False)
    assert resolve_secrets.resolve("jwt_secret") == 1


def test_resolve_secrets_reports_loaded_when_env_set(monkeypatch) -> None:
    from encryption import resolve_secrets

    monkeypatch.setenv("JWT_SECRET", "a-real-signing-key")
    assert resolve_secrets.resolve("jwt_secret") == 0


def test_kms_twin_schema_has_both_clouds_for_every_job() -> None:
    assert check_kms_twin_main() == 0


def test_encrypt_at_rest_round_trips(tmp_path) -> None:
    blob = tmp_path / "jwt.enc"
    encrypt_at_rest.encrypt_blob(b"jwt-demo-value", blob)
    assert encrypt_at_rest.decrypt_blob(blob) == b"jwt-demo-value"


def test_encrypt_at_rest_fails_closed_without_a_key(monkeypatch) -> None:
    monkeypatch.delenv("LOCAL_FERNET_KEY", raising=False)
    with pytest.raises(SystemExit):
        encrypt_at_rest.load_key()
