# LNbits Agent Wallet MCP

A small stdio MCP server for the LNbits `agent_wallet` extension runtime API.

This project is intentionally narrow. It is **not** a generic LNbits wallet MCP and it does **not** use LNbits invoice/admin wallet keys. It only calls the LNbits `agent_wallet` extension's profile-scoped runtime endpoints. The `agent_wallet` extension remains the security boundary: profile lookup, ACL bearer-token authentication, policy enforcement, wallet selection, payment execution, and audit logging all happen inside LNbits.

## Getting started

1. Install the `agent_wallet` extension in LNbits.
2. Create an agent profile in the extension.
3. Copy the MCP config from the extension.
4. Paste the config into your MCP client config.

That's it — your MCP client can now use the LNbits agent wallet tools.

## What It Exposes

The MCP surface is intentionally small:

- `get_status` — read profile status, policy, budget/capabilities summary
- `create_invoice` — request a receive invoice
- `dry_run_payment` — validate a payment/LNURL action without executing it
- `pay_invoice` — request payment of a BOLT11 invoice
- `pay_lightning_address` — request payment to a Lightning address
- `claim_lnurl_withdraw` — claim an LNURL-withdraw into the bound receive wallet
- `list_activity` — read recent agent activity/audit events

`claim_lnurl_withdraw` accepts an optional `amount_sats`. If omitted, the `agent_wallet` runtime resolves the LNURL-withdraw request and uses `maxWithdrawable`.

## Requirements

You need:

1. An LNbits instance with the `agent_wallet` extension installed and configured.
2. An `agent_wallet` profile ID for the agent you want this MCP server to use.
3. A restricted `agent_wallet` ACL bearer token for that profile.
4. [`uv`](https://docs.astral.sh/uv/) installed on the machine running your MCP client.

## Configuration

Required environment variables:

- `LNBITS_URL` — LNbits base URL, for example `https://lnbits.example.com`
- `LNBITS_AGENT_TOKEN` — restricted `agent_wallet` ACL bearer token
- `LNBITS_AGENT_PROFILE_ID` — `agent_wallet` profile ID to scope runtime requests

Optional environment variables:

- `LNBITS_AGENT_TIMEOUT` — request timeout in seconds, default `30`
- `LNBITS_AGENT_RUNTIME_BASE_PATH` — defaults to `/agent_wallet/api/v1`

Authentication is always sent as:

```http
Authorization: Bearer <LNBITS_AGENT_TOKEN>
```

## Install From Git With uvx

Use `uvx` to run the package directly from git. This keeps the project uvx-ready without requiring a manual clone or package install.

```bash
LNBITS_URL=https://your-lnbits.example \
LNBITS_AGENT_TOKEN=restricted-runtime-token \
LNBITS_AGENT_PROFILE_ID=agent-wallet-profile-id \
uvx --from git+https://github.com/lnbits/lnbits-agent-wallet-mcp.git \
  lnbits-agent-wallet-mcp
```

For a pinned revision, use:

```bash
uvx --from git+https://github.com/lnbits/lnbits-agent-wallet-mcp.git@<commit-sha> \
  lnbits-agent-wallet-mcp
```

This is a stdio MCP server. When launched directly it waits for an MCP client on stdin/stdout; it is normal for it not to print a CLI help screen.

## Quick Setup

1. Open the LNbits `agent_wallet` extension.
2. Create or select the agent profile you want this MCP server to use.
3. Copy the profile ID and restricted ACL bearer token from the extension's MCP/connector output.
4. Open your MCP client's configuration file or MCP connector UI.
5. Add a server named `lnbits_agent_wallet` using the command, arguments, and environment variables below.
6. Restart or reload your MCP client.
7. Ask the client to list MCP tools. You should see tools such as `get_status`, `create_invoice`, and `pay_invoice`.

## MCP Connector Configuration

Most MCP clients need the same connector shape: a command, arguments, and environment variables.

Use this JSON shape for clients such as Claude Desktop, Codex, OpenCode/OpenClaw, and other MCP-compatible hosts when they accept JSON server configuration:

```json
{
  "mcpServers": {
    "lnbits_agent_wallet": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/lnbits/lnbits-agent-wallet-mcp.git",
        "lnbits-agent-wallet-mcp"
      ],
      "env": {
        "LNBITS_URL": "https://your-lnbits.example",
        "LNBITS_AGENT_TOKEN": "restricted-runtime-token",
        "LNBITS_AGENT_PROFILE_ID": "agent-wallet-profile-id"
      }
    }
  }
}
```

Replace the three placeholder values with the values from your LNbits `agent_wallet` extension.

### Claude Desktop / JSON-Based Clients

Paste the JSON block above into the client's MCP server configuration. For Claude Desktop, this usually means adding it under `mcpServers` in the Claude desktop config file, then restarting Claude.

### Codex / OpenCode / OpenClaw

Use the same server definition if your client supports MCP JSON configuration. If the client has a UI instead of a file, enter:

- Server name: `lnbits_agent_wallet`
- Command: `uvx`
- Arguments: `--from`, `git+https://github.com/lnbits/lnbits-agent-wallet-mcp.git`, `lnbits-agent-wallet-mcp`
- Environment variables: `LNBITS_URL`, `LNBITS_AGENT_TOKEN`, `LNBITS_AGENT_PROFILE_ID`

### Hermes Example

Hermes uses YAML configuration:

```yaml
mcp_servers:
  lnbits_agent_wallet:
    command: uvx
    args:
      - --from
      - git+https://github.com/lnbits/lnbits-agent-wallet-mcp.git
      - lnbits-agent-wallet-mcp
    env:
      LNBITS_URL: https://your-lnbits.example
      LNBITS_AGENT_TOKEN: restricted-runtime-token
      LNBITS_AGENT_PROFILE_ID: agent-wallet-profile-id
```

### Local Development Checkout

Use this only while developing from a local clone:

```yaml
mcp_servers:
  lnbits_agent_wallet:
    command: uvx
    args:
      - --from
      - /path/to/lnbits-agent-wallet-mcp
      - lnbits-agent-wallet-mcp
    env:
      LNBITS_URL: https://your-lnbits.example
      LNBITS_AGENT_TOKEN: restricted-runtime-token
      LNBITS_AGENT_PROFILE_ID: agent-wallet-profile-id
```

## Expected LNbits Endpoints

Default paths are profile-scoped and intentionally narrow:

- `GET /agent_wallet/api/v1/profiles/{profile_id}/runtime/status`
- `POST /agent_wallet/api/v1/profiles/{profile_id}/runtime/invoice`
- `POST /agent_wallet/api/v1/profiles/{profile_id}/runtime/dry-run`
- `POST /agent_wallet/api/v1/profiles/{profile_id}/runtime/pay`
- `GET /agent_wallet/api/v1/profiles/{profile_id}/activity`

The wrapper never calls `/api/v1/payments` directly.

## Development Checks

```bash
uv run ruff check .
uv run pytest -q
uv build
```
