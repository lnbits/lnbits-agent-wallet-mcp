from __future__ import annotations

import pytest

from lnbits_agent_wallet_mcp.client import AgentWalletClient
from lnbits_agent_wallet_mcp.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(  # type: ignore[arg-type]
        LNBITS_URL="https://lnbits.example.com",
        LNBITS_AGENT_TOKEN="test-token",
        LNBITS_AGENT_PROFILE_ID="profile-123",
    )


@pytest.mark.asyncio
async def test_runtime_paths_are_profile_scoped(settings: Settings) -> None:
    client = AgentWalletClient(settings)
    try:
        assert (
            client._runtime_path("/status")
            == "/agent_wallet/api/v1/profiles/profile-123/runtime/status"
        )
        assert client._activity_path() == "/agent_wallet/api/v1/profiles/profile-123/activity"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_authorization_header_default(settings: Settings) -> None:
    client = AgentWalletClient(settings)
    try:
        assert client._headers() == {
            "Accept": "application/json",
            "Authorization": "Bearer test-token",
        }
    finally:
        await client.close()


def test_profile_id_is_required() -> None:
    settings = Settings(  # type: ignore[arg-type]
        LNBITS_URL="https://lnbits.example.com",
        LNBITS_AGENT_TOKEN="test-token",
    )
    with pytest.raises(ValueError, match="LNBITS_AGENT_PROFILE_ID"):
        AgentWalletClient(settings)
