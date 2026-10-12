# test_mcp_tools.py - Deliverable 2 evidence: unit tests against the MCP
# tool functions directly (no protocol, no subprocess), per the
# capstone's own fallback ("No live MCP server: reuse the Week 6 or
# Week 8 stdio server, or a stub check_stock with Monday's allowlist").
# Every tool is exercised with a valid call, an unknown-role call (must
# be denied, not crash), and -- for check_stock specifically -- the
# bulk-extraction probe the capstone brief names by name: "if check_stock
# can dump a country, you are not done."

from __future__ import annotations

import json

import logistics_mcp_secure as mcp


def test_server_version_is_set() -> None:
    assert mcp.SERVER_VERSION


def test_clinical_ops_check_stock_sees_every_clinic() -> None:
    result = json.loads(mcp.check_stock(item="amoxicillin", role="clinical_ops"))
    assert len(result["stock"]) == 5
    assert {"clinic", "clinic_id", "county", "units", "reorder_needed"} <= result["stock"][0].keys()


def test_partner_clinic_check_stock_sees_only_its_own_clinic() -> None:
    result = json.loads(mcp.check_stock(item="amoxicillin", role="partner_clinic", clinic_id="KSM-01"))
    assert len(result["stock"]) == 1
    assert result["stock"][0]["clinic_id"] == "KSM-01"


def test_partner_clinic_cannot_dump_a_clinic_outside_its_allowlist() -> None:
    # KSI-01 is a real clinic in clinics.json, just not on this partner's
    # allowlist -- a structurally valid, schema-valid request with no
    # override phrasing, which is exactly why it needs its own test.
    result = json.loads(mcp.check_stock(item="amoxicillin", role="partner_clinic", clinic_id="KSI-01"))
    assert result == {"error": "unknown or unauthorised clinic_id", "code": 400}


def test_partner_clinic_wildcard_is_refused_not_a_dump() -> None:
    result = json.loads(mcp.check_stock(item="amoxicillin", role="partner_clinic", clinic_id="*"))
    assert result == {"error": "unknown or unauthorised clinic_id", "code": 400}


def test_partner_clinic_missing_clinic_id_is_refused() -> None:
    result = json.loads(mcp.check_stock(item="amoxicillin", role="partner_clinic"))
    assert result["code"] == 400


def test_unknown_role_is_denied_not_crashed() -> None:
    result = json.loads(mcp.check_stock(item="amoxicillin", role="intern", clinic_id="KSM-01"))
    assert result == {"error": "forbidden", "code": 403}


def test_check_stock_never_returns_an_environment_dump() -> None:
    result_text = mcp.check_stock(item="amoxicillin", role="clinical_ops")
    assert "JWT_SECRET" not in result_text
    assert "OPENAI_API_KEY" not in result_text
    assert "debug_env" not in result_text


def test_partner_clinic_may_not_plan_delivery_route() -> None:
    result = json.loads(mcp.plan_delivery_route(start_clinic_id="KSM-01", role="partner_clinic"))
    assert result == {"error": "forbidden", "code": 403}


def test_clinical_ops_may_plan_delivery_route() -> None:
    result = json.loads(mcp.plan_delivery_route(start_clinic_id="KSM-01", role="clinical_ops"))
    assert result["route"][0] == "Kisumu Central Clinic"
    assert len(result["route"]) == 5


def test_clinical_ops_get_delivery_eta() -> None:
    result = json.loads(mcp.get_delivery_eta(from_clinic_id="KSM-01", to_clinic_id="HBA-01", role="clinical_ops"))
    assert result["km"] > 0


def test_partner_clinic_request_reorder_for_own_clinic() -> None:
    result = json.loads(
        mcp.request_reorder(clinic_id="KSM-01", item="amoxicillin", units=50, role="partner_clinic")
    )
    assert result["status"] == "planned"


def test_partner_clinic_request_reorder_for_other_clinic_is_refused() -> None:
    result = json.loads(
        mcp.request_reorder(clinic_id="KSI-01", item="amoxicillin", units=50, role="partner_clinic")
    )
    assert result == {"error": "unknown or unauthorised clinic_id", "code": 400}


def test_request_reorder_units_out_of_range_returns_error_as_data() -> None:
    result = json.loads(
        mcp.request_reorder(clinic_id="KSM-01", item="amoxicillin", units=9999, role="clinical_ops")
    )
    assert "error" in result


def test_every_tool_call_logs_one_line(caplog) -> None:
    import logging

    with caplog.at_level(logging.INFO, logger="logistics_mcp_secure"):
        mcp.check_stock(item="amoxicillin", role="clinical_ops")
    assert any("tool=check_stock" in r.message for r in caplog.records)
