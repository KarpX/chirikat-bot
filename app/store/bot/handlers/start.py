from aiogram.fsm.context import FSMContext

from aiogram import Router
from aiogram.filters import CommandStart

from app.store.bot.handlers.form import FormState

router = Router()

@router.message(CommandStart())
async def start_handler(message, state: FSMContext):
    await message.answer("Чирик и добро пожаловать!" \
    "\nДля начала создадим анкету...")
    await state.set_state(FormState.name)
    await message.answer("Как к тебе обращаться?")