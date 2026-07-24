from __future__ import annotations

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.keyboards import (
    cancel_button_keyboard,
    main_menu_keyboard,
    muscle_group_keyboard,
    skip_button_keyboard,
)
from bot.services.api_client import ApiClientError, api_client
from bot.services.telegram_helpers import safe_edit_text
from bot.services.user_lookup import get_backend_user_id
from bot.states import WorkoutStates

logger = logging.getLogger(__name__)
router = Router()


def _with_cancel(markup: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    markup.inline_keyboard.append([InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")])
    return markup


@router.callback_query(WorkoutStates.choosing_type, F.data == "type_gym")
async def choose_gym_type(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(workout_type="gym")
    await state.set_state(WorkoutStates.gym_exercise_name)
    await safe_edit_text(
        callback.message,
        "Введите название упражнения:",
        reply_markup=cancel_button_keyboard(),
    )
    await callback.answer()


@router.callback_query(WorkoutStates.choosing_type, F.data == "type_run")
async def choose_run_type(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(workout_type="run")
    await state.set_state(WorkoutStates.run_distance)
    await safe_edit_text(
        callback.message,
        "Введите дистанцию бега в километрах:",
        reply_markup=cancel_button_keyboard(),
    )
    await callback.answer()


@router.callback_query(WorkoutStates.choosing_type, F.data == "type_swim")
async def choose_swim_type(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(workout_type="swim")
    await state.set_state(WorkoutStates.swim_distance)
    await safe_edit_text(
        callback.message,
        "Введите дистанцию плавания в метрах:",
        reply_markup=cancel_button_keyboard(),
    )
    await callback.answer()


@router.message(WorkoutStates.gym_exercise_name)
async def gym_exercise_name(message: Message, state: FSMContext) -> None:
    exercise_name = message.text.strip() if message.text else ""
    if not exercise_name:
        await message.answer("Пожалуйста, введите название упражнения.", reply_markup=cancel_button_keyboard())
        return

    await state.update_data(exercise_name=exercise_name)
    await state.set_state(WorkoutStates.gym_muscle_group)
    await message.answer(
        "Выберите группу мышц:",
        reply_markup=_with_cancel(muscle_group_keyboard()),
    )


@router.callback_query(WorkoutStates.gym_muscle_group, F.data.startswith("muscle_"))
async def gym_muscle_group(callback: CallbackQuery, state: FSMContext) -> None:
    muscle_group = callback.data.removeprefix("muscle_")
    await state.update_data(muscle_group=muscle_group)
    await state.set_state(WorkoutStates.gym_sets)
    await callback.message.edit_text(
        "Введите количество подходов:",
        reply_markup=cancel_button_keyboard(),
    )
    await callback.answer()


@router.message(WorkoutStates.gym_sets)
async def gym_sets(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите количество подходов числом.", reply_markup=cancel_button_keyboard())
        return

    try:
        sets = int(message.text.strip())
        if sets <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительное целое число.", reply_markup=cancel_button_keyboard())
        return

    await state.update_data(sets=sets)
    await state.set_state(WorkoutStates.gym_reps)
    await message.answer("Введите количество повторений в одном подходе:", reply_markup=cancel_button_keyboard())


@router.message(WorkoutStates.gym_reps)
async def gym_reps(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите количество повторений числом.", reply_markup=cancel_button_keyboard())
        return

    try:
        reps = int(message.text.strip())
        if reps <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительное целое число.", reply_markup=cancel_button_keyboard())
        return

    await state.update_data(reps=reps)
    await state.set_state(WorkoutStates.gym_weight)
    await message.answer("Введите вес в килограммах:", reply_markup=cancel_button_keyboard())


@router.message(WorkoutStates.gym_weight)
async def gym_weight(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите вес числом.", reply_markup=cancel_button_keyboard())
        return

    try:
        weight_kg = float(message.text.strip())
        if weight_kg < 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите неотрицательное число.", reply_markup=cancel_button_keyboard())
        return

    await state.update_data(weight_kg=weight_kg)
    await state.set_state(WorkoutStates.common_duration)
    await message.answer("Введите общую продолжительность тренировки в минутах:", reply_markup=cancel_button_keyboard())


@router.message(WorkoutStates.run_distance)
async def run_distance(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите дистанцию числом.", reply_markup=cancel_button_keyboard())
        return

    try:
        distance_km = float(message.text.strip())
        if distance_km <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительное число.", reply_markup=cancel_button_keyboard())
        return

    await state.update_data(distance_km=distance_km)
    await state.set_state(WorkoutStates.run_duration_time)
    await message.answer("Введите длительность пробежки в минутах:", reply_markup=cancel_button_keyboard())


@router.message(WorkoutStates.run_duration_time)
async def run_duration_time(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите длительность числом.", reply_markup=cancel_button_keyboard())
        return

    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительное целое число.", reply_markup=cancel_button_keyboard())
        return

    await state.update_data(run_duration_min=duration)
    await state.set_state(WorkoutStates.run_elevation)
    await message.answer(
        "Введите набор высоты в метрах или нажмите Пропустить:",
        reply_markup=_with_cancel(skip_button_keyboard("skip_elevation")),
    )


@router.callback_query(WorkoutStates.run_elevation, F.data == "skip_elevation")
async def run_elevation_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(elevation_m=None)
    await state.set_state(WorkoutStates.common_duration)
    await safe_edit_text(
        callback.message,
        "Введите общую продолжительность тренировки в минутах:",
        reply_markup=cancel_button_keyboard(),
    )
    await callback.answer()


@router.message(WorkoutStates.run_elevation)
async def run_elevation(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите набор высоты числом или нажмите Пропустить.", reply_markup=_with_cancel(skip_button_keyboard("skip_elevation")))
        return

    try:
        elevation_m = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите целое число.", reply_markup=_with_cancel(skip_button_keyboard("skip_elevation")))
        return

    await state.update_data(elevation_m=elevation_m)
    await state.set_state(WorkoutStates.common_duration)
    await message.answer("Введите общую продолжительность тренировки в минутах:", reply_markup=cancel_button_keyboard())


@router.message(WorkoutStates.swim_distance)
async def swim_distance(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите дистанцию числом.", reply_markup=cancel_button_keyboard())
        return

    try:
        distance_m = int(message.text.strip())
        if distance_m <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительное целое число.", reply_markup=cancel_button_keyboard())
        return

    await state.update_data(distance_m=distance_m)
    await state.set_state(WorkoutStates.swim_pool_length)
    pool_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="25 м", callback_data="pool_25")],
        [InlineKeyboardButton(text="50 м", callback_data="pool_50")],
    ])
    await message.answer(
        "Выберите длину бассейна:",
        reply_markup=_with_cancel(pool_keyboard),
    )


@router.callback_query(WorkoutStates.swim_pool_length, F.data.startswith("pool_"))
async def swim_pool_length(callback: CallbackQuery, state: FSMContext) -> None:
    pool_length_m = int(callback.data.removeprefix("pool_"))
    await state.update_data(pool_length_m=pool_length_m)
    await state.set_state(WorkoutStates.swim_strokes)
    await safe_edit_text(
        callback.message,
        "Введите количество гребков или нажмите Пропустить:",
        reply_markup=_with_cancel(skip_button_keyboard("skip_swim_strokes")),
    )
    await callback.answer()


@router.callback_query(WorkoutStates.swim_strokes, F.data == "skip_swim_strokes")
async def swim_strokes_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(strokes=None)
    await state.set_state(WorkoutStates.swim_heart_rate)
    await safe_edit_text(
        callback.message,
        "Введите средний пульс или нажмите Пропустить:",
        reply_markup=_with_cancel(skip_button_keyboard("skip_swim_heart_rate")),
    )
    await callback.answer()


@router.message(WorkoutStates.swim_strokes)
async def swim_strokes(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите количество гребков числом или нажмите Пропустить.", reply_markup=_with_cancel(skip_button_keyboard("skip_swim_strokes")))
        return

    try:
        strokes = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите целое число или нажмите Пропустить.", reply_markup=_with_cancel(skip_button_keyboard("skip_swim_strokes")))
        return

    await state.update_data(strokes=strokes)
    await state.set_state(WorkoutStates.swim_heart_rate)
    await message.answer(
        "Введите средний пульс или нажмите Пропустить:",
        reply_markup=_with_cancel(skip_button_keyboard("skip_swim_heart_rate")),
    )


@router.callback_query(WorkoutStates.swim_heart_rate, F.data == "skip_swim_heart_rate")
async def swim_heart_rate_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(avg_heart_rate=None)
    await state.set_state(WorkoutStates.common_duration)
    await safe_edit_text(
        callback.message,
        "Введите общую продолжительность тренировки в минутах:",
        reply_markup=cancel_button_keyboard(),
    )
    await callback.answer()


@router.message(WorkoutStates.swim_heart_rate)
async def swim_heart_rate(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите средний пульс числом или нажмите Пропустить.", reply_markup=_with_cancel(skip_button_keyboard("skip_swim_heart_rate")))
        return

    try:
        avg_heart_rate = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите целое число или нажмите Пропустить.", reply_markup=_with_cancel(skip_button_keyboard("skip_swim_heart_rate")))
        return

    await state.update_data(avg_heart_rate=avg_heart_rate)
    await state.set_state(WorkoutStates.common_duration)
    await message.answer("Введите общую продолжительность тренировки в минутах:", reply_markup=cancel_button_keyboard())


@router.message(WorkoutStates.common_duration)
async def common_duration(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите длительность числом.", reply_markup=cancel_button_keyboard())
        return

    try:
        duration_min = int(message.text.strip())
        if duration_min <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите положительное целое число.", reply_markup=cancel_button_keyboard())
        return

    await state.update_data(duration_min=duration_min)
    await state.set_state(WorkoutStates.common_notes)
    await message.answer(
        "Введите заметки о тренировке или нажмите Пропустить:",
        reply_markup=_with_cancel(skip_button_keyboard("skip_notes")),
    )


@router.callback_query(WorkoutStates.common_notes, F.data == "skip_notes")
async def common_notes_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(notes=None)
    await _finalize_workout(callback, state)
    await callback.answer()


@router.message(WorkoutStates.common_notes)
async def common_notes(message: Message, state: FSMContext) -> None:
    notes = message.text.strip() if message.text else None
    await state.update_data(notes=notes)
    await _finalize_workout(message, state)


async def _finalize_workout(event: CallbackQuery | Message, state: FSMContext) -> None:
    data = await state.get_data()
    telegram_id = None
    if isinstance(event, CallbackQuery):
        telegram_id = event.from_user.id if event.from_user else None
    else:
        telegram_id = event.from_user.id if event.from_user else None

    backend_user_id = await get_backend_user_id(telegram_id) if telegram_id is not None else None
    if backend_user_id is None:
        if isinstance(event, CallbackQuery):
            await safe_edit_text(event.message, "Не удалось определить зарегистрированного пользователя.", reply_markup=main_menu_keyboard())
            await event.answer()
        else:
            await event.answer("Не удалось определить зарегистрированного пользователя.", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    backend_user_id = backend_user_id
    workout_type = data.get("workout_type")
    payload: dict[str, object | int | str | None | list[dict[str, object]]] = {
        "type": workout_type,
        "date": datetime.now().isoformat(),
        "duration_min": data["duration_min"],
        "notes": data.get("notes"),
        "user_id": backend_user_id,
    }

    if workout_type == "gym":
        payload["gym_sets"] = [
            {
                "exercise_name": data["exercise_name"],
                "muscle_group": data["muscle_group"],
                "sets": data["sets"],
                "reps": data["reps"],
                "weight_kg": data["weight_kg"],
            }
        ]
        payload["run_session"] = None
        payload["swim_session"] = None
    elif workout_type == "run":
        run_duration_min = data["run_duration_min"]
        distance_km = data["distance_km"]
        avg_pace = run_duration_min / distance_km
        payload["gym_sets"] = None
        payload["run_session"] = {
            "distance_km": distance_km,
            "avg_pace_min_km": avg_pace,
            "elevation_m": data.get("elevation_m"),
            "route_name": None,
        }
        payload["swim_session"] = None
    elif workout_type == "swim":
        payload["gym_sets"] = None
        payload["run_session"] = None
        payload["swim_session"] = {
            "distance_m": data["distance_m"],
            "pool_length_m": data["pool_length_m"],
            "strokes": data.get("strokes"),
            "avg_heart_rate": data.get("avg_heart_rate"),
        }
    else:
        if isinstance(event, CallbackQuery):
            await event.message.edit_text("Ошибка обработки данных тренировки.", reply_markup=main_menu_keyboard())
            await event.answer()
        else:
            await event.answer("Ошибка обработки данных тренировки.", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    try:
        await api_client.create_workout(workout_data=payload)
    except ApiClientError:
        logger.exception("Failed to create workout")
        if isinstance(event, CallbackQuery):
            await event.message.edit_text("Не удалось сохранить тренировку. Попробуйте позже.", reply_markup=main_menu_keyboard())
            await event.answer()
        else:
            await event.answer("Не удалось сохранить тренировку. Попробуйте позже.", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    summary_lines = [
        "Тренировка сохранена!",
        f"Тип: {workout_type}",
        f"Длительность: {data['duration_min']} мин",
    ]
    if workout_type == "gym":
        summary_lines.append(
            f"Упражнение: {data['exercise_name']}, группа: {data['muscle_group']}, подходов: {data['sets']}, повторений: {data['reps']}, вес: {data['weight_kg']} кг"
        )
    elif workout_type == "run":
        summary_lines.append(
            f"Дистанция: {data['distance_km']} км, средний темп: {payload['run_session']['avg_pace_min_km']:.2f} мин/км"
        )
        if data.get("elevation_m") is not None:
            summary_lines.append(f"Набор высоты: {data['elevation_m']} м")
    elif workout_type == "swim":
        summary_lines.append(
            f"Дистанция: {data['distance_m']} м, длина бассейна: {data['pool_length_m']} м"
        )
        if data.get("strokes") is not None:
            summary_lines.append(f"Гребков: {data['strokes']}")
        if data.get("avg_heart_rate") is not None:
            summary_lines.append(f"Пульс: {data['avg_heart_rate']}")
    if data.get("notes"):
        summary_lines.append(f"Заметки: {data['notes']}")

    if isinstance(event, CallbackQuery):
        await event.message.edit_text("\n".join(summary_lines), reply_markup=main_menu_keyboard())
        await event.answer()
    else:
        await event.answer("\n".join(summary_lines), reply_markup=main_menu_keyboard())

    await state.clear()
