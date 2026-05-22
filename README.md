# lnbits-agent-wallet-mcp

Tiny, scoped MCP server for LNbits `agent_wallet` runtime actions.

This is the narrow Agent Wallet MCP, not the broad/generic LNbits MCP. It deliberately
does **not** call LNbits core wallet endpoints and does **not** need invoice/admin
wallet keys. It only calls designated `agent_wallet` runtime endpoints. `agent_wallet`
remains the security boundary: profile lookup, policy enforcement, wallet selection,
payment execution, and audit logging all happen inside LNbits.

## what it exposes

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

## required configuration

Environment variables:

- `LNBITS_URL` — LNbits base URL, e.g. `https://example.com`
- `LNBITS_AGENT_TOKEN` — restricted agent/runtime token
- `LNBITS_AGENT_PROFILE_ID` — Agent Wallet profile id to scope runtime requests

Optional environment variables:

- `LNBITS_AGENT_TIMEOUT` — request timeout in seconds, default `30`
- `LNBITS_AGENT_AUTH_HEADER` — `authorization` by default, or `x-api-key`
- `LNBITS_AGENT_RUNTIME_BASE_PATH` — defaults to `/agent_wallet/api/v1`

## use from git with uvx

After this repo is pushed to GitHub, the intended production-style launch is:

```bash
LNBITS_URL=https://your-lnbits.example \
LNBITS_AGENT_TOKEN=restricted-runtime-token \
LNBITS_AGENT_PROFILE_ID=agent-wallet-profile-id \
uvx --from git+https://github.com/talvasconcelos/lnbits-agent-wallet-mcp.git \
  lnbits-agent-wallet-mcp
```

For a pinned revision, use:

```bash
uvx --from git+https://github.com/talvasconcelos/lnbits-agent-wallet-mcp.git@<commit-sha> \
  lnbits-agent-wallet-mcp
```

This is a stdio MCP server, so it normally waits for an MCP client on stdin/stdout. It
does not print a CLI help screen.

## Hermes config from git

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

## Hermes config from a local checkout

Use this while developing locally:

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

## run locally

```bash
uv run lnbits-agent-wallet-mcp
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

## local uvx smoke test

Before pushing, you can verify the package is uvx-installable from the checkout:

```bash
timeout 3s env \
  LNBITS_URL=https://lnbits.example.com \
  LNBITS_AGENT_TOKEN=test-token \
  LNBITS_AGENT_PROFILE_ID=profile-123 \
  uvx --from file://$PWD lnbits-agent-wallet-mcp
```

Expected result: `timeout` exits with code `124` after three seconds and no error output.
That means the package installed, the console script started, and the stdio MCP server
waited for client input.
