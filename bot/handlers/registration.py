from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Contact, Message

from bot.keyboards import main_menu_keyboard, share_contact_keyboard
from bot.services.api_client import ApiClientError, api_client
from bot.states import RegistrationStates

logger = logging.getLogger(__name__)
router = Router()

REGISTERED_USERS: dict[int, int] = {}


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    telegram_id = message.from_user.id if message.from_user else None
    if telegram_id is None:
        await message.answer("Не удалось определить ваш Telegram ID.")
        return

    if telegram_id in REGISTERED_USERS:
        await message.answer("С возвращением!", reply_markup=main_menu_keyboard())
        return

    await state.set_state(RegistrationStates.waiting_for_contact)
    await message.answer("Добро пожаловать в FitTrack! Чтобы продолжить, поделитесь контактом.", reply_markup=share_contact_keyboard())


@router.message(RegistrationStates.waiting_for_contact, F.content_type == "contact")
async def handle_contact(message: Message, state: FSMContext) -> None:
    contact = message.contact
    if not isinstance(contact, Contact):
        await message.answer("Пожалуйста, поделитесь контактом через кнопку ниже.")
        return

    telegram_id = contact.user_id or message.from_user.id if message.from_user else None
    if telegram_id is None:
        await message.answer("Не удалось получить ваш Telegram ID.")
        return

    username = message.from_user.username if message.from_user and message.from_user.username else (message.from_user.first_name if message.from_user else "user")
    email = f"tg{telegram_id}@fittrack.local"

    try:
        existing_user = await api_client.get_user_by_telegram_id(telegram_id)
        if existing_user is not None:
            backend_user_id = existing_user["id"]
        else:
            user_data = await api_client.create_user(
                username=username,
                email=email,
                phone_number=contact.phone_number,
                telegram_id=telegram_id,
            )
            backend_user_id = user_data["id"]
    except ApiClientError:
        logger.exception("Failed to look up or register user")
        await message.answer("Не удалось зарегистрироваться. Попробуйте позже.")
        return

    REGISTERED_USERS[telegram_id] = backend_user_id
    await state.clear()
    await message.answer("Регистрация завершена. Добро пожаловать в FitTrack!", reply_markup=main_menu_keyboard())
