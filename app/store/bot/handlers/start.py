import random

from aiogram.fsm.context import FSMContext

from aiogram import Router
from aiogram.filters import CommandStart

from app.store.bot.builders import send_form_message
from app.store.bot.handlers.form import FormState
from app.user.accessor import userAccessor
from app.forms.accessor import formAccessor

router = Router()

@router.message(CommandStart())
async def start_handler(message, state: FSMContext):
    user = await userAccessor.create_or_get_user(message.from_user.id, message.from_user.username)
    form = await formAccessor.get_form_by_user_id(user.id)
    if form:
        if not form.enabled:
            await formAccessor.update_form(message.from_user.id, **{"enabled" : True})

        await message.answer(f"Чирик, @{user.username}! С возвращением в гнездо\n\nПока ты отсутствовал, мы съели все крошки\nМожешь поспрашивать у остальных – может что осталось?")
        await send_form_message(message, form)
        return

    await message.answer("Чирик и добро пожаловать!" \
    "\nДля начала создадим анкету...")
    await state.set_state(FormState.name)
    await message.answer("Как к тебе обращаться?")