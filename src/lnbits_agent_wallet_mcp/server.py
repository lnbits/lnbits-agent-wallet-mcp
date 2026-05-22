from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Awaitable, Callable
from typing import Any

from mcp import types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from . import __version__
from .client import AgentWalletClient, AgentWalletError
from .config import get_settings
from .tools import TOOLS

ToolHandler = Callable[[AgentWalletClient, dict[str, Any]], Awaitable[Any]]


class ToolArgumentError(ValueError):
    """Raised when an MCP tool call is missing required arguments."""


def _json_text(data: Any) -> list[types.TextContent]:
    return [
        types.TextContent(
            type="text",
            text=json.dumps(data, indent=2, sort_keys=True, default=str),
        )
    ]


def _required_str(args: dict[str, Any], name: str) -> str:
    value = args.get(name)
    if not isinstance(value, str) or not value:
        raise ToolArgumentError(f"{name} is required")
    return value


def _optional_positive_int(args: dict[str, Any], name: str) -> int | None:
    value = args.get(name)
    if value is None:
        return None
    if not isinstance(value, int) or value < 1:
        raise ToolArgumentError(f"{name} must be a positive integer")
    return value


def _required_positive_int(args: dict[str, Any], name: str) -> int:
    value = _optional_positive_int(args, name)
    if value is None:
        raise ToolArgumentError(f"{name} is required")
    return value


def _runtime_payment_payload(
    *,
    action: str,
    destination: str,
    amount_sats: int | None = None,
    payment_request: str | None = None,
    comment: str | None = None,
    dry_run_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action": action,
        "destination": destination,
    }
    if amount_sats is not None:
        payload["amount_sats"] = amount_sats
    if payment_request:
        payload["payment_request"] = payment_request
    if comment:
        payload["comment"] = comment
    if dry_run_id:
        payload["dry_run_id"] = dry_run_id
    return payload


async def _get_status(client: AgentWalletClient, _: dict[str, Any]) -> Any:
    return await client.get_runtime("/status")


async def _create_invoice(client: AgentWalletClient, args: dict[str, Any]) -> Any:
    payload = {
        "amount_sats": _required_positive_int(args, "amount_sats"),
    }
    if args.get("memo"):
        payload["memo"] = args["memo"]
    if args.get("expiry") is not None:
        payload["expiry"] = _required_positive_int(args, "expiry")
    return await client.post_runtime("/invoice", payload)


async def _dry_run_payment(client: AgentWalletClient, args: dict[str, Any]) -> Any:
    action = args.get("action") or "bolt11"
    payment_request = _required_str(args, "payment_request")
    destination = args.get("destination") or payment_request
    amount_sats = _optional_positive_int(args, "amount_sats")
    if action != "lnurl_withdraw" and amount_sats is None:
        raise ToolArgumentError("amount_sats is required unless action is lnurl_withdraw")
    payload = _runtime_payment_payload(
        action=action,
        amount_sats=amount_sats,
        destination=destination,
        payment_request=payment_request,
        comment=args.get("comment"),
    )
    return await client.post_runtime("/dry-run", payload)


async def _pay_invoice(client: AgentWalletClient, args: dict[str, Any]) -> Any:
    bolt11 = _required_str(args, "bolt11")
    payload = _runtime_payment_payload(
        action="bolt11",
        amount_sats=_required_positive_int(args, "amount_sats"),
        destination=bolt11,
        payment_request=bolt11,
        comment=args.get("memo"),
        dry_run_id=args.get("dry_run_id"),
    )
    return await client.post_runtime("/pay", payload)


async def _pay_lightning_address(client: AgentWalletClient, args: dict[str, Any]) -> Any:
    address = _required_str(args, "lightning_address")
    payload = _runtime_payment_payload(
        action="lightning_address",
        amount_sats=_required_positive_int(args, "amount_sats"),
        destination=address,
        payment_request=address,
        comment=args.get("comment"),
        dry_run_id=args.get("dry_run_id"),
    )
    return await client.post_runtime("/pay", payload)


async def _claim_lnurl_withdraw(client: AgentWalletClient, args: dict[str, Any]) -> Any:
    lnurl = _required_str(args, "lnurl")
    payload = _runtime_payment_payload(
        action="lnurl_withdraw",
        amount_sats=_optional_positive_int(args, "amount_sats"),
        destination=lnurl,
        payment_request=lnurl,
        comment=args.get("comment"),
    )
    return await client.post_runtime("/pay", payload)


async def _list_activity(client: AgentWalletClient, args: dict[str, Any]) -> Any:
    params: dict[str, int] = {}
    limit = args.get("limit")
    offset = args.get("offset")
    if limit is not None:
        params["limit"] = _required_positive_int(args, "limit")
    if offset is not None:
        if not isinstance(offset, int) or offset < 0:
            raise ToolArgumentError("offset must be a non-negative integer")
        params["offset"] = offset
    return await client.get_activity(params or None)


HANDLERS: dict[str, ToolHandler] = {
    "get_status": _get_status,
    "create_invoice": _create_invoice,
    "dry_run_payment": _dry_run_payment,
    "pay_invoice": _pay_invoice,
    "pay_lightning_address": _pay_lightning_address,
    "claim_lnurl_withdraw": _claim_lnurl_withdraw,
    "list_activity": _list_activity,
}


class LNbitsAgentMCPServer:
    """MCP server exposing only scoped agent_wallet runtime actions."""

    def __init__(self, client: AgentWalletClient | None = None):
        self.server = Server("lnbits-agent-wallet-mcp")
        self.client = client or AgentWalletClient(get_settings())
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            return TOOLS

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            handler = HANDLERS.get(name)
            if handler is None:
                return _json_text({"error": f"Unknown tool: {name}"})

            try:
                result = await handler(self.client, arguments or {})
                return _json_text(result)
            except (AgentWalletError, ToolArgumentError) as exc:
                return _json_text({"error": str(exc)})
            except Exception as exc:  # noqa: BLE001 - MCP errors must be serialized
                return _json_text({"error": f"Unexpected MCP server error: {exc}"})

    async def run(self) -> None:
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="lnbits-agent-wallet-mcp",
                        server_version=__version__,
                        capabilities=types.ServerCapabilities(
                            tools=types.ToolsCapability(listChanged=False),
                        ),
                    ),
                )
        finally:
            await self.client.close()


async def async_main() -> None:
    server = LNbitsAgentMCPServer()
    await server.run()


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass
    except Exception as exc:  # keep stdout clean for MCP stdio
        print(f"lnbits-agent-wallet-mcp failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
