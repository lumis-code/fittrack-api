from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.config import BOT_TOKEN
from bot.handlers import ai, menu, registration, stats, workout

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def register_handlers() -> None:
    dp.include_router(registration.router)
    dp.include_router(menu.router)
    dp.include_router(workout.router)
    dp.include_router(stats.router)
    dp.include_router(ai.router)


async def main() -> None:
    register_handlers()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())


# Example webhook setup for later deployment:
# from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
# from aiohttp import web
#
# async def on_startup(bot: Bot) -> None:
#     await bot.set_webhook("https://your-domain.com/webhook")
#
# app = web.Application()
# app.router.add_post("/webhook", SimpleRequestHandler(dispatcher=dp, bot=bot))
# setup_application(app, dp, bot=bot)
