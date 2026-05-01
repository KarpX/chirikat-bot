from aiogram import F, Router

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.store.bot.builders import BotButtons, SympathyButtons, build_reply_keyboard, send_form_message, send_got_sympathy_message, send_match_message, send_search_form_message
from app.forms.accessor import formAccessor
from app.user.accessor import userAccessor

class SympathyState(StatesGroup):
    choose_button_sympathy = State()
    got_sympathies = State()
    see_matches = State()

router = Router()

@router.message(F.text == BotButtons.SYMPATHIES.value)
async def handle_sympathies(message: Message, state: FSMContext):
    sympathies = await formAccessor.get_sympathy_forms(message.from_user.id)

    await state.set_state(SympathyState.choose_button_sympathy)

    await message.answer("Что ты хочешь посмотреть?\n"
    f"Новых симпатий: {len(sympathies)}", reply_markup=build_reply_keyboard(
        [{"text": SympathyButtons.GOT_SYMPATHIES.value}, {"text": SympathyButtons.SEE_MATCHES.value}, {"text": SympathyButtons.BACK.value}],
        adjust=[2, 2]
    ))

@router.message(SympathyState.choose_button_sympathy, F.text == SympathyButtons.GOT_SYMPATHIES.value)
async def handle_got_sympathies(message: Message, state: FSMContext):
    await state.set_state(SympathyState.got_sympathies)
    sympathies = await formAccessor.get_sympathy_forms(message.from_user.id)

    if not sympathies:
        await message.answer("У тебя нет новых симпатий.")
        return

    for form in sympathies:
        await send_got_sympathy_message(message, form)

    await state.set_state(SympathyState.choose_button_sympathy)
    await handle_sympathies(message, state)

@router.message(SympathyState.choose_button_sympathy, F.text == SympathyButtons.SEE_MATCHES.value)
async def handle_see_matches(message: Message, state: FSMContext):
    await state.set_state(SympathyState.see_matches)
    matches = await formAccessor.get_matches(message.from_user.id)

    if not matches:
        await message.answer("У тебя нет взаимных симпатий")
        return

    for match in matches:
        target_form = match if match.user_id != message.from_user.id else None
        target_user = await userAccessor.get_user(user_id=target_form.user_id)
        if target_form is not None:
            await send_match_message(message, target_form, target_user.username)

    await state.set_state(SympathyState.choose_button_sympathy)
    await handle_sympathies(message, state)

@router.message(SympathyState.choose_button_sympathy, F.text == SympathyButtons.BACK.value)
async def handle_back(message: Message, state: FSMContext):
    form = await formAccessor.get_form_by_user_id(message.from_user.id)

    if form:
        await send_form_message(message, form)

    await state.clear()
    