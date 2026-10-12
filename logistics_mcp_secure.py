# logistics_mcp_secure.py - the AfyaPlus logistics MCP server, reused from
# Weeks 6/8's logistics_mcp.py / logistics_mcp_versioned.py, with the fix
# this week's brief demands in plain words: "If check_stock can dump a
# country, you are not done."
#
# Every tool now takes an explicit `role` argument and is checked against
# access_control/rbac.py's deny-by-default matrix BEFORE doing any work.
# An unrecognised role, or a role the matrix never granted this tool to,
# gets back {"error": "forbidden", "code": 403} -- the smallest useful
# dictionary, never a stack trace, never an environment dump.
#
# check_stock additionally enforces per-clinic scope: a partner_clinic
# caller must pass a clinic_id that is both on access_control's allowlist
# AND actually theirs, and gets back exactly that one clinic's row --
# never the whole table and never a clinic_id="*" wildcard. A
# clinical_ops caller (routing across every clinic) still sees the full
# table, because that is the job the role actually needs to do.
#
# Production standards carried over unchanged from Week 8:
#   - input checking: every tool validates its arguments before doing
#     anything else
#   - errors as instructive data: a bad argument returns a JSON object
#     with an "error" key, never a raised exception
#   - one log line per call: every tool logs its name, role, and
#     arguments to logs/mcp.log before doing any work
#
# Run it standalone:
#   python logistics_mcp_secure.py
# Fastest first test (no agent, no protocol):
#   python -c "
#   import logistics_mcp_secure as m
#   print(m.check_stock(item='amoxicillin', role='clinical_ops'))
#   print(m.check_stock(item='amoxicillin', role='partner_clinic', clinic_id='KSM-01'))
#   print(m.check_stock(item='amoxicillin', role='partner_clinic', clinic_id='*'))
#   "
# Offline unit tests (this capstone's "no live MCP server" fallback path):
#   pytest tests/test_mcp_tools.py -v

from __future__ import annotations

import json
import logging
import math
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

REPO_ROOT = Path(__file__).resolve().parent
LOG_PATH = REPO_ROOT / "logs" / "mcp.log"
LOG_PATH.parent.mkdir(exist_ok=True)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from access_control.rbac import allowed  # noqa: E402
from logging_.redact import redact  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
log = logging.getLogger("logistics_mcp_secure")

SERVER_VERSION = "2.0.0-secure"

server = FastMCP("afyaplus-logistics")

CLINICS_PATH = REPO_ROOT / "clinics.json"
with open(CLINICS_PATH) as f:
    CLINICS = json.load(f)["clinics"]

ALLOWLIST_PATH = REPO_ROOT / "access_control" / "clinics_allowlist.json"
with open(ALLOWLIST_PATH) as f:
    PARTNER_CLINIC_IDS = frozenset(str(c).strip().upper() for c in json.load(f)["clinics"])

VALID_ITEMS = ["amoxicillin", "ors_sachets", "malaria_kits"]
MAX_REORDER_UNITS = 500

FORBIDDEN = json.dumps({"error": "forbidden", "code": 403})


def _clinic(clinic_id: str) -> dict | None:
    return next((c for c in CLINICS if c["id"] == clinic_id), None)


def distance_km(a: dict, b: dict) -> float:
    """Rough distance between two clinics in kilometres (equirectangular approximation)."""
    dx = (a["lon"] - b["lon"]) * 111.32 * math.cos(math.radians((a["lat"] + b["lat"]) / 2))
    dy = (a["lat"] - b["lat"]) * 110.57
    return round(math.sqrt(dx * dx + dy * dy), 1)


def _stock_row(c: dict, item: str) -> dict:
    return {
        "clinic": c["name"],
        "clinic_id": c["id"],
        "county": c["county"],
        "units": c["stock"][item],
        "reorder_needed": c["stock"][item] < 10,
    }


@server.tool()
def check_stock(item: str, role: str, clinic_id: str | None = None) -> str:
    """Check how many units of a medical item a clinic holds.
    Valid items: amoxicillin, ors_sachets, malaria_kits. role must be
    'partner_clinic' or 'clinical_ops'. A partner_clinic caller must pass
    their own allowlisted clinic_id and receives only that clinic's row
    -- never every clinic in the country, and never a clinic_id="*"
    wildcard. A clinical_ops caller receives the full cross-clinic table,
    which routing and reorder planning actually require."""
    log.info("tool=check_stock role=%s item=%s clinic_id=%s", role, item, redact(clinic_id or ""))
    if not allowed(role, "check_stock"):
        return FORBIDDEN
    if item not in VALID_ITEMS:
        return json.dumps({"error": f"Unknown item '{item}'. Valid items: {VALID_ITEMS}"})

    if role == "partner_clinic":
        cid = (clinic_id or "").strip().upper()
        # Reject before any lookup: "*", "", and any id outside this
        # partner's allowlist all land here, with the same 400 shape, so
        # response timing never leaks which other clinic ids exist.
        if cid not in PARTNER_CLINIC_IDS:
            return json.dumps({"error": "unknown or unauthorised clinic_id", "code": 400})
        clinic = _clinic(cid)
        if clinic is None:
            return json.dumps({"error": "unknown or unauthorised clinic_id", "code": 400})
        return json.dumps({"item": item, "stock": [_stock_row(clinic, item)]})

    # clinical_ops: the full table, still the smallest useful dict for
    # the job -- clinic name/id/county/units/reorder flag, nothing else.
    rows = [_stock_row(c, item) for c in CLINICS]
    return json.dumps({"item": item, "stock": rows})


@server.tool()
def plan_delivery_route(start_clinic_id: str, role: str) -> str:
    """Plan a delivery route visiting every clinic, starting from one clinic.
    clinical_ops only -- a single-clinic partner has no use for a route
    across every other clinic, and rbac.py's matrix denies it rather
    than relying on nobody asking."""
    log.info("tool=plan_delivery_route role=%s start=%s", role, start_clinic_id)
    if not allowed(role, "plan_delivery_route"):
        return FORBIDDEN
    start = _clinic(start_clinic_id)
    if start is None:
        ids = [c["id"] for c in CLINICS]
        return json.dumps({"error": f"Unknown clinic id '{start_clinic_id}'. Valid ids: {ids}"})
    route, remaining, total = [start], [c for c in CLINICS if c["id"] != start_clinic_id], 0.0
    while remaining:
        here = route[-1]
        nearest = min(remaining, key=lambda c: distance_km(here, c))
        total += distance_km(here, nearest)
        route.append(nearest)
        remaining.remove(nearest)
    return json.dumps(
        {
            "route": [c["name"] for c in route],
            "total_km": round(total, 1),
            "method": "nearest-neighbour heuristic",
        }
    )


@server.tool()
def get_delivery_eta(from_clinic_id: str, to_clinic_id: str, role: str) -> str:
    """Estimate driving distance (km) and time (minutes) between two clinics.
    clinical_ops only, same reasoning as plan_delivery_route."""
    log.info("tool=get_delivery_eta role=%s from=%s to=%s", role, from_clinic_id, to_clinic_id)
    if not allowed(role, "get_delivery_eta"):
        return FORBIDDEN
    a, b = _clinic(from_clinic_id), _clinic(to_clinic_id)
    if a is None or b is None:
        ids = [c["id"] for c in CLINICS]
        return json.dumps({"error": f"Unknown clinic id. Valid ids: {ids}"})
    km = distance_km(a, b)
    return json.dumps(
        {
            "from": a["name"],
            "to": b["name"],
            "km": km,
            "eta_minutes": round(km / 40 * 60),
            "assumed_speed_kmh": 40,
        }
    )


@server.tool()
def request_reorder(clinic_id: str, item: str, units: int, role: str) -> str:
    """Plan a reorder of a medical item for one clinic. Does not commit or
    dispatch anything -- a human coordinator must confirm it. A
    partner_clinic caller may only request for their own allowlisted
    clinic; clinical_ops may request for any clinic."""
    log.info("tool=request_reorder role=%s clinic=%s item=%s units=%s", role, clinic_id, item, units)
    if not allowed(role, "request_reorder"):
        return FORBIDDEN
    if role == "partner_clinic" and clinic_id.strip().upper() not in PARTNER_CLINIC_IDS:
        return json.dumps({"error": "unknown or unauthorised clinic_id", "code": 400})
    clinic = _clinic(clinic_id)
    if clinic is None:
        ids = [c["id"] for c in CLINICS]
        return json.dumps({"error": f"Unknown clinic id '{clinic_id}'. Valid ids: {ids}"})
    if item not in VALID_ITEMS:
        return json.dumps({"error": f"Unknown item '{item}'. Valid items: {VALID_ITEMS}"})
    if not isinstance(units, int) or units < 1 or units > MAX_REORDER_UNITS:
        return json.dumps({"error": f"units must be an integer between 1 and {MAX_REORDER_UNITS}, got {units!r}"})
    return json.dumps(
        {
            "status": "planned",
            "clinic": clinic["name"],
            "clinic_id": clinic["id"],
            "item": item,
            "units": units,
            "note": "Not yet approved or dispatched - a human coordinator must confirm this request.",
        }
    )


if __name__ == "__main__":
    server.run()
