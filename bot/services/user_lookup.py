from __future__ import annotations

from bot.handlers.registration import REGISTERED_USERS
from bot.services.api_client import ApiClientError, api_client


async def get_backend_user_id(telegram_id: int) -> int | None:
    """Get backend user_id for a telegram_id, checking cache first then live lookup."""
    if telegram_id in REGISTERED_USERS:
        return REGISTERED_USERS[telegram_id]

    try:
        user = await api_client.get_user_by_telegram_id(telegram_id)
    except ApiClientError:
        return None

    if user is None:
        return None

    REGISTERED_USERS[telegram_id] = user["id"]
    return REGISTERED_USERS[telegram_id]
