"""Deliverable 2: application-level authorisation, including MCP.

A valid JWT proves who is calling (authentication). It says nothing
about what they may do (authorisation) -- that is a second, separate
check, enforced here as a role-to-tool matrix rather than assumed to
follow automatically from a successful login.

partner_clinic is a partner-facing role (their own clinic's stock,
their own clinic's reorders); clinical_ops is an internal operations
role (routing and ETAs across every clinic, on top of stock and
reorders). logistics_mcp_secure.py imports allowed() directly and calls
it before doing any work for every tool.
"""

TOOLS_BY_ROLE = {
    "partner_clinic": {"check_stock", "request_reorder"},
    "clinical_ops": {"check_stock", "plan_delivery_route", "get_delivery_eta", "request_reorder"},
}


def allowed(role: str, tool: str) -> bool:
    """Deny-by-default: an unrecognised role gets an empty set from the
    dictionary default, so every membership test against it is False --
    a behaviour, not a policy statement someone has to remember to
    apply. Without the default, an unknown role would raise KeyError,
    and the fix people reach for under pressure is a try/except that
    quietly returns True to make the error go away."""
    return tool in TOOLS_BY_ROLE.get(role, set())


if __name__ == "__main__":
    assert allowed("partner_clinic", "check_stock") is True
    assert allowed("clinical_ops", "plan_delivery_route") is True
    # A partner must never reach the routing tool -- authentication is
    # not authorisation.
    assert allowed("partner_clinic", "plan_delivery_route") is False
    # An unknown role is a denial, not a KeyError.
    assert allowed("intern", "check_stock") is False
    # dump_all is absent from the matrix entirely, so it is denied to
    # everybody -- a debugging tool that was never added can never leak.
    assert not any(allowed(r, "dump_all") for r in TOOLS_BY_ROLE)
    print("rbac OK", len(TOOLS_BY_ROLE), "roles, deny-by-default holds")
