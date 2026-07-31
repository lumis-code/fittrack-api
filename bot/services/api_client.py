from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from bot.config import API_BASE_URL

logger = logging.getLogger(__name__)


class ApiClientError(Exception):
    """Raised when the backend request fails."""


class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        # Ensure BOT_SERVICE_TOKEN is loaded from bot/.env (bot.config already calls load_dotenv)
        self.bot_service_token = os.getenv("BOT_SERVICE_TOKEN")
        if not self.bot_service_token:
            raise RuntimeError("BOT_SERVICE_TOKEN not set in bot .env")

    async def _request(self, method: str, path: str, *, json_body: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        headers = {"X-Bot-Token": self.bot_service_token}
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.request(method, url, json=json_body, params=params, headers=headers)
        except httpx.TimeoutException as exc:
            raise ApiClientError(f"Request to {url} timed out") from exc

        if not response.is_success:
            body = response.text or "<empty>"
            raise ApiClientError(f"Backend request failed ({response.status_code}): {body}")

        try:
            if response.content:
                return response.json()
            return None
        except ValueError as exc:
            raise ApiClientError(f"Backend returned invalid JSON: {response.text}") from exc

    async def create_user(self, *, username: str, email: str, phone_number: str, telegram_id: int) -> dict[str, Any]:
        payload = {
            "username": username,
            "email": email,
            "phone_number": phone_number,
            "telegram_id": telegram_id,
        }
        return await self._request("POST", "/bot/users", json_body=payload)

    async def get_user_by_telegram_id(self, telegram_id: int) -> dict[str, Any] | None:
        """Look up a registered user by telegram_id. Returns None if not found."""
        try:
            return await self._request("GET", f"/bot/users/telegram/{telegram_id}")
        except ApiClientError as exc:
            if "404" in str(exc):
                return None
            raise

    async def create_workout(self, *, workout_data: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/bot/workouts", json_body=workout_data)

    async def get_user_stats(self, user_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/bot/users/{user_id}/stats")

    async def get_recent_workouts(self, user_id: int, limit: int = 1) -> list[dict[str, Any]]:
        return await self._request("GET", "/bot/workouts", params={"user_id": user_id, "limit": limit})

    async def analyze_workout(self, workout_id: int) -> dict[str, Any]:
        return await self._request("POST", f"/bot/ai/analyze/{workout_id}")

    async def get_weekly_plan(self, *, user_id: int, goal: str | None = None) -> dict[str, Any]:
        payload = {"user_id": user_id, "goal": goal}
        return await self._request("POST", "/bot/ai/weekly-plan", json_body=payload)


api_client = ApiClient()
