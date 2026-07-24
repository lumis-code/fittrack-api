from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.keyboards import main_menu_keyboard, workout_type_keyboard
from bot.services.telegram_helpers import safe_edit_text
from bot.services.user_lookup import get_backend_user_id
from bot.states import WorkoutStates

router = Router()


@router.callback_query(F.data == "log_workout")
async def start_workout_flow(callback: CallbackQuery, state: FSMContext) -> None:
    telegram_id = callback.from_user.id if callback.from_user else None
    backend_user_id = await get_backend_user_id(telegram_id) if telegram_id is not None else None
    if backend_user_id is None:
        await safe_edit_text(callback.message, "Сначала зарегистрируйтесь.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    await state.set_state(WorkoutStates.choosing_type)
    await safe_edit_text(callback.message, "Выберите тип тренировки:", reply_markup=workout_type_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit_text(callback.message, "Операция отменена.", reply_markup=main_menu_keyboard())
    await callback.answer()
