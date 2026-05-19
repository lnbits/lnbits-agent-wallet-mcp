from __future__ import annotations

from lnbits_agent_mcp.server import HANDLERS, _runtime_payment_payload
from lnbits_agent_mcp.tools import TOOLS


def test_all_tools_have_handlers() -> None:
    names = {tool.name for tool in TOOLS}
    assert names == set(HANDLERS)


def test_tool_surface_is_small() -> None:
    assert len(TOOLS) == 6


def test_payment_payload_matches_agent_wallet_runtime_model() -> None:
    payload = _runtime_payment_payload(
        action="bolt11",
        amount_sats=21,
        destination="lnbc...",
        payment_request="lnbc...",
        comment="test",
        dry_run_id="dry-run-123",
    )
    assert payload == {
        "action": "bolt11",
        "amount_sats": 21,
        "destination": "lnbc...",
        "payment_request": "lnbc...",
        "comment": "test",
        "dry_run_id": "dry-run-123",
    }


def test_optional_payment_fields_are_omitted_when_empty() -> None:
    payload = _runtime_payment_payload(
        action="lightning_address",
        amount_sats=21,
        destination="tal@example.com",
    )
    assert payload == {
        "action": "lightning_address",
        "amount_sats": 21,
        "destination": "tal@example.com",
    }
