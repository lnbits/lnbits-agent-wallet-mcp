from __future__ import annotations

from typing import Any

import httpx

from .config import Settings


class AgentWalletError(Exception):
    """Raised when agent_wallet returns an error response."""


class AgentWalletClient:
    """Small HTTP client for the agent_wallet runtime API."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = str(settings.lnbits_url).rstrip("/")
        self.runtime_base = settings.runtime_base_path.rstrip("/")
        self.profile_id = settings.profile_id
        if not self.profile_id:
            raise ValueError("LNBITS_AGENT_PROFILE_ID is required for agent_wallet runtime API")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=settings.timeout,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.settings.token}",
        }

    def _runtime_path(self, path: str) -> str:
        return f"{self.runtime_base}/profiles/{self.profile_id}/runtime{path}"

    def _activity_path(self) -> str:
        return f"{self.runtime_base}/profiles/{self.profile_id}/activity"

    async def close(self) -> None:
        await self._client.aclose()

    async def get_runtime(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = await self._client.get(self._runtime_path(path), params=params)
        return self._handle_response(response)

    async def post_runtime(self, path: str, payload: dict[str, Any]) -> Any:
        response = await self._client.post(self._runtime_path(path), json=payload)
        return self._handle_response(response)

    async def get_activity(self, params: dict[str, Any] | None = None) -> Any:
        response = await self._client.get(self._activity_path(), params=params)
        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.is_success:
            if not response.content:
                return {"success": True}
            return response.json()

        try:
            body: Any = response.json()
        except ValueError:
            body = response.text
        raise AgentWalletError(
            f"agent_wallet API error {response.status_code}: {body}"
        )
