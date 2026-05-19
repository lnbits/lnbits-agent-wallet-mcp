# lnbits-agent-mcp

Tiny, scoped MCP server for LNbits `agent_wallet` runtime actions.

The server deliberately does **not** talk to LNbits core wallet endpoints and does **not**
need invoice/admin wallet keys. It only calls designated `agent_wallet` runtime
endpoints. `agent_wallet` remains the security boundary: profile lookup, policy
enforcement, wallet selection, payment execution, and audit logging all happen inside
LNbits.

## tools

- `get_status` — profile status, policy, budget/capabilities summary
- `create_invoice` — request a receive invoice
- `dry_run_payment` — validate a payment request without executing it
- `pay_invoice` — request payment of a BOLT11 invoice
- `pay_lightning_address` — request payment to a lightning address
- `list_activity` — read recent agent activity/audit events

## configuration

Environment variables:

- `LNBITS_URL` — LNbits base URL, e.g. `https://example.com`
- `LNBITS_AGENT_TOKEN` — restricted agent/runtime token
- `LNBITS_AGENT_PROFILE_ID` — agent_wallet profile id to scope runtime requests
- `LNBITS_AGENT_TIMEOUT` — optional request timeout, default `30`

## run locally

```bash
uv run lnbits-agent-mcp
```

## uvx from git

```yaml
mcp_servers:
  lnbits_agent:
    command: uvx
    args:
      - --from
      - git+https://github.com/lnbits/lnbits-agent-mcp.git
      - lnbits-agent-mcp
    env:
      LNBITS_URL: https://your-lnbits.example
      LNBITS_AGENT_TOKEN: restricted-runtime-token
```

## expected LNbits endpoints

Default paths are intentionally narrow:

- `GET /agent_wallet/api/v1/runtime/status`
- `POST /agent_wallet/api/v1/runtime/invoice`
- `POST /agent_wallet/api/v1/runtime/dry-run`
- `POST /agent_wallet/api/v1/runtime/pay/invoice`
- `POST /agent_wallet/api/v1/runtime/pay/lightning-address`
- `GET /agent_wallet/api/v1/runtime/activity`

If `LNBITS_AGENT_PROFILE_ID` is set, it is sent as `profile_id` in requests for
early development compatibility. Long term, prefer token-bound runtime endpoints.
