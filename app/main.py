# main.py - the AfyaPlus triage API, reused from Week 6's
# secure_triage_api.py / further_challenge_c_roles.py / further_challenge_b
# (JWT auth, role gate, rate limit, background audit log) with this
# week's security layer wired into the real request path rather than
# left as standalone demos next to it:
#
#   - importing app.auth calls encryption/boot_guard.py's require() at
#     import time, so the whole service refuses to boot without a real
#     JWT_SECRET (Deliverable 1)
#   - /triage calls access_control/injection_guard.py BEFORE triage_model(),
#     returning a plain 400 on override-style text (Deliverable 2)
#   - /triage keeps Depends(require_role("coordinator")): a valid guest
#     token still earns 403 -- authentication is not authorisation
#     (Deliverable 2)
#   - every /triage call (accepted or refused) writes one redacted,
#     hashed, structured audit line via logging_/redact_then_hash.py,
#     carrying a trace id (Deliverable 3)
#
# Routes:
#   GET  /health  - unprotected; monitoring probes don't log in
#   POST /token   - login, returns a signed JWT
#   POST /triage  - protected + role-gated (coordinator only)
#
# Run it:
#   uvicorn app.main:app --reload --port 8000

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from access_control.injection_guard import triage_or_reject  # noqa: E402
from app.auth import check_password, create_token, require_role  # noqa: E402
from app.models import (  # noqa: E402
    HealthResponse,
    LoginRequest,
    TokenResponse,
    TriageRequest,
    TriageResponse,
)
from app.rate_limit import check_rate_limit  # noqa: E402
from app.triage_model import triage_model  # noqa: E402
from logging_.redact_then_hash import write_audit_line  # noqa: E402

SERVICE_NAME = "afyaplus-triage-api"
SERVICE_VERSION = "2.0.0"

app = FastAPI(title="AfyaPlus Triage API (Secured, Week 9)", version=SERVICE_VERSION)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service=SERVICE_NAME, version=SERVICE_VERSION, status="ok")


@app.post("/token", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    if not check_password(body.username, body.password):
        raise HTTPException(status_code=401, detail="Wrong username or password.")
    return TokenResponse(access_token=create_token(body.username))


@app.post("/triage")
def triage(request: TriageRequest, user: dict = Depends(require_role("coordinator"))):
    # require_role already proved WHO is calling (401 otherwise) and that
    # their role may use this route (403 otherwise) before this body runs.
    trace_id = uuid4().hex[:8]
    check_rate_limit(user["sub"])

    guard = triage_or_reject(request.patient_message)
    if guard.get("code") == 400:
        write_audit_line(
            actor=user["sub"],
            action="triage_rejected",
            resource=request.county,
            outcome=False,
            payload=request.patient_message,
            trace_id=trace_id,
        )
        return JSONResponse(status_code=400, content={"error": "rejected", "trace_id": trace_id})

    result = triage_model(request.patient_message)
    write_audit_line(
        actor=user["sub"],
        action="triage",
        resource=request.county,
        outcome=True,
        payload=request.patient_message,
        trace_id=trace_id,
    )
    return TriageResponse(urgency=result["urgency"], advice=result["advice"], handled_for=user["sub"])
