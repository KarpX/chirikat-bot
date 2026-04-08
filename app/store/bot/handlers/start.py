from aiogram.fsm.context import FSMContext

from aiogram import Router
from aiogram.filters import CommandStart
from sqlalchemy import select

from app.store.bot.handlers.form import FormState
from app.store.database.database import database
from app.user.accessor import userAccessor
from app.user.models import UserModel

router = Router()

@router.message(CommandStart())
async def start_handler(message, state: FSMContext):
    await userAccessor.create_or_get_user(message.from_user.id, message.from_user.username)

    await message.answer("Чирик и добро пожаловать!" \
    "\nДля начала создадим анкету...")
    await state.set_state(FormState.name)
    await message.answer("Как к тебе обращаться?")