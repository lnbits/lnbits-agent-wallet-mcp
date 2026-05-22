from __future__ import annotations

import pytest

from lnbits_agent_wallet_mcp.server import HANDLERS, _dry_run_payment, _runtime_payment_payload
from lnbits_agent_wallet_mcp.tools import TOOLS


class StubClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def post_runtime(self, path: str, payload: dict) -> dict:
        self.calls.append((path, payload))
        return {"ok": True, "payload": payload}


def test_all_tools_have_handlers() -> None:
    names = {tool.name for tool in TOOLS}
    assert names == set(HANDLERS)


def test_tool_surface_is_small_and_curated() -> None:
    assert {tool.name for tool in TOOLS} == {
        "get_status",
        "create_invoice",
        "dry_run_payment",
        "pay_invoice",
        "pay_lightning_address",
        "claim_lnurl_withdraw",
        "list_activity",
    }


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


def test_lnurl_withdraw_payload_can_omit_amount() -> None:
    payload = _runtime_payment_payload(
        action="lnurl_withdraw",
        destination="lightning:LNURL1...",
        payment_request="lightning:LNURL1...",
    )
    assert payload == {
        "action": "lnurl_withdraw",
        "destination": "lightning:LNURL1...",
        "payment_request": "lightning:LNURL1...",
    }


@pytest.mark.asyncio
async def test_dry_run_lnurl_withdraw_allows_missing_amount() -> None:
    client = StubClient()

    response = await _dry_run_payment(
        client,  # type: ignore[arg-type]
        {
            "action": "lnurl_withdraw",
            "payment_request": "lightning:LNURL1...",
        },
    )

    assert response["ok"] is True
    assert client.calls == [
        (
            "/dry-run",
            {
                "action": "lnurl_withdraw",
                "destination": "lightning:LNURL1...",
                "payment_request": "lightning:LNURL1...",
            },
        )
    ]


@pytest.mark.asyncio
async def test_dry_run_spending_requires_amount() -> None:
    client = StubClient()

    with pytest.raises(ValueError, match="amount_sats is required"):
        await _dry_run_payment(
            client,  # type: ignore[arg-type]
            {
                "action": "bolt11",
                "payment_request": "lnbc...",
            },
        )
