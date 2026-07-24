from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def share_contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
    )


def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🏋️ Записать тренировку", callback_data="log_workout")],
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats")],
        [InlineKeyboardButton(text="🤖 AI-анализ последней тренировки", callback_data="ai_analyze_last")],
        [InlineKeyboardButton(text="📅 План на неделю", callback_data="weekly_plan")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workout_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Зал", callback_data="type_gym")],
        [InlineKeyboardButton(text="Бег", callback_data="type_run")],
        [InlineKeyboardButton(text="Плавание", callback_data="type_swim")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def muscle_group_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Грудь", callback_data="muscle_chest")],
        [InlineKeyboardButton(text="Спина", callback_data="muscle_back")],
        [InlineKeyboardButton(text="Ноги", callback_data="muscle_legs")],
        [InlineKeyboardButton(text="Руки", callback_data="muscle_arms")],
        [InlineKeyboardButton(text="Плечи", callback_data="muscle_shoulders")],
        [InlineKeyboardButton(text="Пресс", callback_data="muscle_abs")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def skip_button_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Пропустить", callback_data=callback_data)]])


def cancel_button_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]])
