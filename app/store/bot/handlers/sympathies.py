from asyncio.log import logger

from aiogram import F, Router

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InputMediaPhoto, Message
from aiogram.fsm.context import FSMContext

from app.store.bot.builders import BotButtons, MatchesButtons, SympathyButtons, build_form_text, build_main_keyboard, build_reply_keyboard, send_form_message, send_got_sympathy_message, send_match_message, send_search_form_message
from app.forms.accessor import formAccessor
from app.user.accessor import userAccessor

class SympathyState(StatesGroup):
    choose_button_sympathy = State()
    got_sympathies = State()
    see_matches = State()

router = Router()

@router.message(F.text == BotButtons.SYMPATHIES.value)
async def handle_sympathies(message: Message, state: FSMContext):
    matches = await formAccessor.get_matches(message.from_user.id)
    matches_ids = [f.id for f in matches]
    sympathies = await formAccessor.get_sympathy_forms(message.from_user.id)
    sympathies_list = [f for f in sympathies if f.id not in matches_ids]

    await state.set_state(SympathyState.choose_button_sympathy)

    await message.answer("Что ты хочешь посмотреть?\n"
    f"Новых симпатий: {len(sympathies_list)}", reply_markup=build_reply_keyboard(
        [{"text": SympathyButtons.GOT_SYMPATHIES.value}, {"text": SympathyButtons.SEE_MATCHES.value}, {"text": SympathyButtons.BACK.value}],
        adjust=[2, 2]
    ))

@router.message(SympathyState.choose_button_sympathy, F.text == SympathyButtons.GOT_SYMPATHIES.value)
async def handle_got_sympathies(message: Message, state: FSMContext):
    await state.set_state(SympathyState.got_sympathies)
    matches = await formAccessor.get_matches(message.from_user.id)
    sympathies = await formAccessor.get_sympathy_forms(message.from_user.id)

    if not sympathies:
        await message.answer("У тебя нет новых симпатий.", reply_markup=build_reply_keyboard(
        [{"text": SympathyButtons.GOT_SYMPATHIES.value}, {"text": SympathyButtons.SEE_MATCHES.value}, {"text": SympathyButtons.BACK.value}],
        adjust=[2, 2]
    ))
        await state.set_state(SympathyState.choose_button_sympathy)
        return
    
    matches_ids = [f.id for f in matches]
    forms_data = [{"id": f.user_id, "dist": None} for f in sympathies if f.id not in matches_ids]
    
    await state.set_state(SympathyState.got_sympathies)
    await state.update_data(forms=forms_data, current_index=0)

    await next_sympathy(message, state)

@router.message(SympathyState.got_sympathies, F.text.in_([BotButtons.LIKE.value, BotButtons.SKIP.value, BotButtons.BACK.value]))
async def sympathy_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    index = data.get("current_index", 0)
    forms = data.get("forms", [])

    if index >= len(forms):
        return

    target_item = forms[index]
    target_form = await formAccessor.get_form_by_user_id(target_item["id"])
    my_form = await formAccessor.get_form_by_user_id(message.from_user.id)

    if message.text == BotButtons.BACK.value:
        await state.clear()
        await handle_sympathies(message, state)
        return

    if message.text == BotButtons.SKIP.value:
        await formAccessor.delete_like(from_form_id=target_form.id, to_form_id=my_form.id)
        
    elif message.text == BotButtons.LIKE.value:
        success, is_match = await formAccessor.add_like(message.from_user.id, target_form.id)
        
        if is_match:
            target_user = await userAccessor.get_user(user_id=target_form.user_id)
            my_user = await userAccessor.get_user(user_id=message.from_user.id)

            await send_form_message(message, target_form, username=target_user.username)

            try:
                match_caption = build_form_text(my_form)
                if my_form.images:
                    media = [InputMediaPhoto(media=img.file_id, caption=match_caption if i == 0 else "", parse_mode="HTML") 
                             for i, img in enumerate(my_form.images[:3])]
                    await message.bot.send_media_group(chat_id=target_form.user_id, media=media)
                    await message.bot.send_message(
                        chat_id=target_form.user_id, 
                        text=f"🎉 <b>Это взаимно!</b>\n@{my_user.username} ждет твоего сообщения.", 
                        reply_markup=build_reply_keyboard(build_main_keyboard(), adjust=[2, 2]),
                        parse_mode="HTML"
                    )
                else:
                    await message.bot.send_message(chat_id=target_form.user_id, text=match_caption, parse_mode="HTML")
                    await message.bot.send_message(
                        chat_id=target_form.user_id, 
                        text=f"🎉 <b>Это взаимно!</b>\n@{my_user.username} ждет твоего сообщения.", 
                        reply_markup=build_reply_keyboard(build_main_keyboard(), adjust=[2, 2]),
                        parse_mode="HTML"
                    )
            except Exception as e:
                logger.error(f"Error notifying target match in sympathies: {e}")

    await state.update_data(current_index=index + 1)
    await next_sympathy(message, state)

@router.message(SympathyState.got_sympathies)
async def next_sympathy(message: Message, state: FSMContext):
    data = await state.get_data()

    forms = data.get("forms", [])
    index = data.get("current_index", 0)

    if index >= len(forms):
        message.answer("Это все симпатии!", reply_markup=build_reply_keyboard(
        [{"text": SympathyButtons.GOT_SYMPATHIES.value}, {"text": SympathyButtons.SEE_MATCHES.value}, {"text": SympathyButtons.BACK.value}],
        adjust=[2, 2]
        ))
        await state.clear()
        await handle_sympathies(message, state)
        return
    
    current_item = forms[index]
    target_form = await formAccessor.get_form_by_user_id(current_item["id"])

    target_form.distance_km = current_item["dist"]

    await send_got_sympathy_message(message=message, form=target_form)

@router.message(SympathyState.see_matches, F.text.in_([MatchesButtons.NEXT.value, MatchesButtons.BACK.value]))
async def handle_matches(message: Message, state: FSMContext):
    data = await state.get_data()
    forms = data.get("forms", [])
    index = data.get("current_index", 0)

    if message.text == MatchesButtons.BACK.value:
        await state.clear()
        await handle_sympathies(message, state)
        return

    await state.update_data(current_index=index + 1)
    
    await next_match(message, state)

@router.message(SympathyState.see_matches)
async def next_match(message: Message, state: FSMContext):
    data = await state.get_data()
    forms = data.get("forms", [])
    index = data.get("current_index", 0)

    if index >= len(forms):
        await message.answer("Это все взаимные симпатии!", reply_markup=build_reply_keyboard(
        [{"text": SympathyButtons.GOT_SYMPATHIES.value}, {"text": SympathyButtons.SEE_MATCHES.value}, {"text": SympathyButtons.BACK.value}],
        adjust=[2, 2]
        ))
        await state.clear()
        await handle_sympathies(message, state)
        return
    
    current_item = forms[index]
    target_form = await formAccessor.get_form_by_user_id(current_item["id"])
    target_user = await userAccessor.get_user(user_id=target_form.user_id)

    await send_match_message(message, target_form, target_user.username)


@router.message(SympathyState.choose_button_sympathy, F.text == SympathyButtons.SEE_MATCHES.value)
async def handle_see_matches(message: Message, state: FSMContext):
    await state.set_state(SympathyState.see_matches)
    matches = await formAccessor.get_matches(message.from_user.id)

    if not matches:
        await state.set_state(SympathyState.choose_button_sympathy)
        await message.answer("У тебя нет взаимных симпатий")
        return

    # for match in matches:
    #     target_form = match if match.user_id != message.from_user.id else None
    #     target_user = await userAccessor.get_user(user_id=target_form.user_id)
    #     if target_form is not None:
    #         await send_match_message(message, target_form, target_user.username)

    matches_list = [{"id": f.user_id, "dist": None} for f in matches]
    await state.update_data(forms=matches_list, current_index=0)

    await next_match(message, state)

    # await state.set_state(SympathyState.choose_button_sympathy)
    # await handle_sympathies(message, state)

@router.message(SympathyState.choose_button_sympathy, F.text == SympathyButtons.BACK.value)
async def handle_back(message: Message, state: FSMContext):
    form = await formAccessor.get_form_by_user_id(message.from_user.id)

    if form:
        await send_form_message(message, form)

    await state.clear()
    