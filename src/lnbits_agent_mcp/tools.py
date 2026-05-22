from __future__ import annotations

from typing import Any

from mcp.types import Tool


def _schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


PAYMENT_ACTIONS = ["bolt11", "lnurl_pay", "lightning_address", "lnurl_withdraw"]

_AMOUNT_SATS_SCHEMA = {
    "type": "integer",
    "minimum": 1,
    "description": "Amount in satoshis. Optional for LNURL-withdraw; defaults to maxWithdrawable.",
}

_DRY_RUN_ID_SCHEMA = {
    "type": "string",
    "description": "Approved dry-run activity id, when required by policy.",
}

TOOLS: list[Tool] = [
    Tool(
        name="get_status",
        description=(
            "Get the active agent_wallet runtime profile status, capabilities, "
            "policy limits, and budget summary. Does not mutate state."
        ),
        inputSchema=_schema({}),
    ),
    Tool(
        name="create_invoice",
        description=(
            "Create a Lightning receive invoice through agent_wallet. "
            "agent_wallet selects the bound wallet and logs the action."
        ),
        inputSchema=_schema(
            {
                "amount_sats": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Invoice amount in satoshis.",
                },
                "memo": {
                    "type": "string",
                    "description": "Invoice memo/description.",
                },
                "expiry": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Optional invoice expiry in seconds.",
                },
            },
            ["amount_sats"],
        ),
    ),
    Tool(
        name="dry_run_payment",
        description=(
            "Validate a payment or LNURL-withdraw against agent_wallet policy without "
            "executing it. Use before spending when policy requires dry runs."
        ),
        inputSchema=_schema(
            {
                "payment_request": {
                    "type": "string",
                    "description": "BOLT11 invoice, LNURL, LNURL-withdraw, or lightning address.",
                },
                "amount_sats": _AMOUNT_SATS_SCHEMA,
                "action": {
                    "type": "string",
                    "enum": PAYMENT_ACTIONS,
                    "default": "bolt11",
                },
                "destination": {
                    "type": "string",
                    "description": "Policy destination override; defaults to payment_request.",
                },
                "comment": {"type": "string"},
            },
            ["payment_request"],
        ),
    ),
    Tool(
        name="pay_invoice",
        description=(
            "Request payment of a BOLT11 invoice. agent_wallet enforces policy, "
            "spending limits, approval state, and logs the action."
        ),
        inputSchema=_schema(
            {
                "bolt11": {"type": "string", "description": "BOLT11 invoice."},
                "amount_sats": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Invoice amount in satoshis.",
                },
                "memo": {"type": "string", "description": "Optional internal memo."},
                "dry_run_id": _DRY_RUN_ID_SCHEMA,
            },
            ["bolt11", "amount_sats"],
        ),
    ),
    Tool(
        name="pay_lightning_address",
        description=(
            "Request payment to a lightning address. agent_wallet enforces "
            "domain/address allowlists, spending limits, and logs the action."
        ),
        inputSchema=_schema(
            {
                "lightning_address": {
                    "type": "string",
                    "description": "Address like user@example.com.",
                },
                "amount_sats": {"type": "integer", "minimum": 1},
                "comment": {"type": "string"},
                "dry_run_id": _DRY_RUN_ID_SCHEMA,
            },
            ["lightning_address", "amount_sats"],
        ),
    ),
    Tool(
        name="claim_lnurl_withdraw",
        description=(
            "Claim an LNURL-withdraw into the bound agent_wallet receive wallet. "
            "The amount is optional; when omitted, agent_wallet uses maxWithdrawable."
        ),
        inputSchema=_schema(
            {
                "lnurl": {
                    "type": "string",
                    "description": "LNURL-withdraw string or lightning:LNURL... URI.",
                },
                "amount_sats": _AMOUNT_SATS_SCHEMA,
                "comment": {"type": "string", "description": "Optional invoice memo override."},
            },
            ["lnurl"],
        ),
    ),
    Tool(
        name="list_activity",
        description="List recent agent_wallet runtime activity/audit events.",
        inputSchema=_schema(
            {
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20,
                },
                "offset": {"type": "integer", "minimum": 0, "default": 0},
            }
        ),
    ),
]
