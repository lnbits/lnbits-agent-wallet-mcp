# lnbits-agent-wallet-mcp

Tiny, scoped MCP server for LNbits `agent_wallet` runtime actions.

This server deliberately does **not** call LNbits core wallet endpoints and does **not**
need invoice/admin wallet keys. It only calls designated `agent_wallet` runtime
endpoints. `agent_wallet` remains the security boundary: profile lookup, policy
enforcement, wallet selection, payment execution, and audit logging all happen inside
LNbits.

## tool surface

The MCP surface is intentionally small:

- `get_status` — read profile status, policy, budget/capabilities summary
- `create_invoice` — request a receive invoice
- `dry_run_payment` — validate a payment/LNURL action without executing it
- `pay_invoice` — request payment of a BOLT11 invoice
- `pay_lightning_address` — request payment to a lightning address
- `claim_lnurl_withdraw` — claim an LNURL-withdraw into the bound receive wallet
- `list_activity` — read recent agent activity/audit events

`claim_lnurl_withdraw` accepts an optional `amount_sats`. If omitted, the Agent Wallet
runtime resolves the LNURL-withdraw request and uses `maxWithdrawable`.

## configuration

Environment variables:

- `LNBITS_URL` — LNbits base URL, e.g. `https://example.com`
- `LNBITS_AGENT_TOKEN` — restricted agent/runtime token
- `LNBITS_AGENT_PROFILE_ID` — agent_wallet profile id to scope runtime requests
- `LNBITS_AGENT_TIMEOUT` — optional request timeout, default `30`
- `LNBITS_AGENT_AUTH_HEADER` — `authorization` by default, or `x-api-key`
- `LNBITS_AGENT_RUNTIME_BASE_PATH` — defaults to `/agent_wallet/api/v1`

## run locally

```bash
uv run lnbits-agent-wallet-mcp
```

## Hermes config from a local checkout

```yaml
mcp_servers:
  lnbits_agent_wallet:
    command: uv
    args:
      - --directory
      - /path/to/lnbits-agent-wallet-mcp
      - run
      - lnbits-agent-wallet-mcp
    env:
      LNBITS_URL: https://your-lnbits.example
      LNBITS_AGENT_TOKEN: restricted-runtime-token
      LNBITS_AGENT_PROFILE_ID: agent-wallet-profile-id
```

## uvx from git

```yaml
mcp_servers:
  lnbits_agent_wallet:
    command: uvx
    args:
      - --from
      - git+https://github.com/talvasconcelos/lnbits-agent-wallet-mcp.git
      - lnbits-agent-wallet-mcp
    env:
      LNBITS_URL: https://your-lnbits.example
      LNBITS_AGENT_TOKEN: restricted-runtime-token
      LNBITS_AGENT_PROFILE_ID: agent-wallet-profile-id
```

## expected LNbits endpoints

Default paths are profile-scoped and intentionally narrow:

- `GET /agent_wallet/api/v1/profiles/{profile_id}/runtime/status`
- `POST /agent_wallet/api/v1/profiles/{profile_id}/runtime/invoice`
- `POST /agent_wallet/api/v1/profiles/{profile_id}/runtime/dry-run`
- `POST /agent_wallet/api/v1/profiles/{profile_id}/runtime/pay`
- `GET /agent_wallet/api/v1/profiles/{profile_id}/activity`

The wrapper never calls `/api/v1/payments` directly.

## development checks

```bash
uv run ruff check .
uv run pytest -q
uv build
```
