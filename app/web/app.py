import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.store.bot.handlers import setup_routers
from app.store.database.database import database
from app.store.storage import SQLAlchemyStorage
from app.web.config import load_config

async def main() -> None:
    config = load_config()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout) # Дублировать логи в консоль
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Бот запущен!")

    storage = SQLAlchemyStorage(database)
    dp = Dispatcher(storage=storage)

    bot = Bot(token=config.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await database.connect()
    setup_routers(dp)

    await dp.start_polling(bot)


def run():
    asyncio.run(main())