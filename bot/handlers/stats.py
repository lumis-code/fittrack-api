from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards import main_menu_keyboard
from bot.services.api_client import ApiClientError, api_client
from bot.services.telegram_helpers import safe_edit_text
from bot.services.user_lookup import get_backend_user_id

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "my_stats")
async def handle_my_stats(callback: CallbackQuery) -> None:
    telegram_id = callback.from_user.id if callback.from_user else None
    backend_user_id = await get_backend_user_id(telegram_id) if telegram_id is not None else None
    if backend_user_id is None:
        await safe_edit_text(callback.message, "Сначала зарегистрируйтесь.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return
    try:
        stats = await api_client.get_user_stats(backend_user_id)
    except ApiClientError:
        logger.exception("Failed to fetch user stats")
        await safe_edit_text(callback.message, "Не удалось получить статистику.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    total_workouts = stats.get("total_workouts", 0)
    total_duration_hours = stats.get("total_duration_hours", 0.0)
    total_distance_km = stats.get("total_distance_km", 0.0)
    breakdown = stats.get("breakdown_by_type", {})

    response_text = (
        f"📊 Ваша статистика:\n"
        f"Всего тренировок: {total_workouts}\n"
        f"Общая длительность: {total_duration_hours:.1f} ч\n"
        f"Общая дистанция: {total_distance_km:.1f} км\n"
        f"\n"
        f"Разбивка по типам:\n"
        f"🏋️ Зал: {breakdown.get('gym', 0)}\n"
        f"🏃 Бег: {breakdown.get('run', 0)}\n"
        f"🏊 Плавание: {breakdown.get('swim', 0)}"
    )

    await safe_edit_text(callback.message, response_text, reply_markup=main_menu_keyboard())
    await callback.answer()
