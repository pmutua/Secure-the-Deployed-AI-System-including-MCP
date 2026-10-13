# auth.py - JWT authentication, reused from Week 6's secure_triage_api.py
# and Week 6's further_challenge_c_roles.py (role gate) with one change
# for this week: SECRET_KEY now comes from encryption/boot_guard.py's
# require(), not a dev-only fallback. Importing this module is the app's
# actual boot path -- if JWT_SECRET is missing or blank, the import
# raises SystemExit before a single route can be registered. "Security
# adds authorisation and input checks, it does not remove
# authentication": current_user() and require_role() are unchanged in
# shape from Week 6.

from __future__ import annotations

import sys
import time
from pathlib import Path

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from encryption.boot_guard import require  # noqa: E402

SECRET_KEY = require("JWT_SECRET")  # fails closed (Deliverable 1) -- no default
ALGORITHM = "HS256"
TOKEN_LIFETIME_SECONDS = 30 * 60  # 30 minutes

# Two demo accounts, matching the two roles the API distinguishes:
#   - mercy (coordinator): may triage patients
#   - guest (viewer): may authenticate, but a valid guest token still
#     earns a 403 on /triage -- authentication is not authorisation.
USERS: dict[str, dict[str, object]] = {
    "mercy": {
        "password_hash": bcrypt.hashpw(b"logistics2026", bcrypt.gensalt()),
        "role": "coordinator",
    },
    "guest": {
        "password_hash": bcrypt.hashpw(b"lookaround", bcrypt.gensalt()),
        "role": "viewer",
    },
}


def check_password(username: str, password: str) -> bool:
    user = USERS.get(username)
    if user is None:
        return False
    return bcrypt.checkpw(password.encode(), user["password_hash"])


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "role": USERS[username]["role"],
        "exp": int(time.time()) + TOKEN_LIFETIME_SECONDS,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    """FastAPI dependency: verifies the Bearer token before the endpoint body runs.

    auto_error=False on HTTPBearer, plus the explicit check below, is
    what makes a missing Authorization header a 401 and not FastAPI's
    HTTPBearer default of 403 -- "no credentials offered" and "credentials
    offered but invalid" are both authentication failures, so both must
    be 401; only a VALID token for the wrong role earns 403
    (require_role, below). A present-but-bad token (expired, or altered
    so its signature no longer matches) becomes a clean 401 here instead
    of leaking a jwt.decode exception as an unhandled 500.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
    return payload


def require_role(role: str):
    """Dependency factory: current_user() answers WHO is calling; this
    answers what that identity is ALLOWED to do. A valid token for the
    wrong role earns 403, not 401 -- different failures, different fixes."""

    def _check(user: dict = Depends(current_user)) -> dict:
        if user["role"] != role:
            raise HTTPException(status_code=403, detail=f"Your role may not use this endpoint (requires '{role}').")
        return user

    return _check
