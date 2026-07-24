from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.keyboards import main_menu_keyboard, workout_type_keyboard
from bot.states import WorkoutStates

router = Router()


@router.callback_query(F.data == "log_workout")
async def start_workout_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WorkoutStates.choosing_type)
    await callback.message.edit_text("Выберите тип тренировки:", reply_markup=workout_type_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Операция отменена.", reply_markup=main_menu_keyboard())
    await callback.answer()
