import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.store.bot.handlers import setup_routers
from app.web.config import load_config

dp = Dispatcher()

async def main() -> None:
    config = load_config()
    bot = Bot(token=config.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    setup_routers(dp)

    await dp.start_polling(bot)

def run():
    asyncio.run(main())