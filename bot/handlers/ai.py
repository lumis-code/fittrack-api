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


@router.callback_query(F.data == "ai_analyze_last")
async def handle_ai_analyze_last(callback: CallbackQuery) -> None:
    telegram_id = callback.from_user.id if callback.from_user else None
    backend_user_id = await get_backend_user_id(telegram_id) if telegram_id is not None else None
    if backend_user_id is None:
        await safe_edit_text(callback.message, "Сначала зарегистрируйтесь.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return
    await safe_edit_text(callback.message, "⏳ Анализирую...")
    await callback.answer()

    try:
        workouts = await api_client.get_recent_workouts(backend_user_id, limit=1)
    except ApiClientError:
        logger.exception("Failed to fetch recent workouts")
        await safe_edit_text(callback.message, "Не удалось получить последние тренировки.", reply_markup=main_menu_keyboard())
        return

    if not workouts:
        await safe_edit_text(callback.message, "У вас пока нет тренировок.", reply_markup=main_menu_keyboard())
        return

    workout_id = workouts[0].get("id")
    if workout_id is None:
        await safe_edit_text(callback.message, "Не удалось определить последнюю тренировку.", reply_markup=main_menu_keyboard())
        return

    try:
        analysis = await api_client.analyze_workout(workout_id)
    except ApiClientError:
        logger.exception("Failed to analyze workout")
        await safe_edit_text(callback.message, "Не удалось проанализировать тренировку.", reply_markup=main_menu_keyboard())
        return

    response_text = analysis.get("response", "AI не вернул результат.")
    await safe_edit_text(callback.message, response_text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "weekly_plan")
async def handle_weekly_plan(callback: CallbackQuery) -> None:
    telegram_id = callback.from_user.id if callback.from_user else None
    backend_user_id = await get_backend_user_id(telegram_id) if telegram_id is not None else None
    if backend_user_id is None:
        await safe_edit_text(callback.message, "Сначала зарегистрируйтесь.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return
    await safe_edit_text(callback.message, "⏳ Генерирую план...")
    await callback.answer()

    try:
        plan = await api_client.get_weekly_plan(user_id=backend_user_id, goal=None)
    except ApiClientError as exc:
        logger.exception("Failed to generate weekly plan")
        error_text = str(exc)
        if "Not enough" in error_text:
            await safe_edit_text(callback.message, "Недостаточно истории тренировок.", reply_markup=main_menu_keyboard())
        else:
            await safe_edit_text(callback.message, "Не удалось сгенерировать план.", reply_markup=main_menu_keyboard())
        return

    response_text = plan.get("response", "AI не вернул результат.")
    await safe_edit_text(callback.message, response_text, reply_markup=main_menu_keyboard())
