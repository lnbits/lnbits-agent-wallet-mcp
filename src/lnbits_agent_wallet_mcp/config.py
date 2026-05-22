from __future__ import annotations

from functools import lru_cache
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the MCP server."""

    model_config = SettingsConfigDict(env_prefix="LNBITS_AGENT_", extra="ignore")

    # Uses explicit alias so the shared LNbits convention is LNBITS_URL, not
    # LNBITS_AGENT_LNBITS_URL.
    lnbits_url: AnyHttpUrl = Field(alias="LNBITS_URL")
    token: str = Field(alias="LNBITS_AGENT_TOKEN")
    profile_id: str | None = Field(default=None, alias="LNBITS_AGENT_PROFILE_ID")
    timeout: float = Field(default=30.0, alias="LNBITS_AGENT_TIMEOUT")
    runtime_base_path: str = Field(
        default="/agent_wallet/api/v1",
        alias="LNBITS_AGENT_RUNTIME_BASE_PATH",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
