import logging
import time

from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from aiogram.fsm.context import FSMContext

from app.forms.accessor import formAccessor
from app.store.bot.builders import BotButtons, InlineButtons, LikeButtons, build_form_text, build_inline_keyboard, build_main_keyboard, build_reply_keyboard, send_form_message, send_search_form_message
from app.user.accessor import userAccessor

logger = logging.getLogger(__name__)

router = Router()

class SearchState(StatesGroup):
    viewing = State()
    settings = State()
    gender_settings = State()

@router.message(F.text == BotButtons.SEARCH.value)
async def search_handler(message: Message, state: FSMContext):
    await message.answer("Ищем для тебя самых лучших!")
    await state.set_state(SearchState.viewing)
    await show_next_form(message, state)

@router.message(SearchState.viewing, F.text == BotButtons.LIKE.value)
async def searh_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    forms = data.get("forms", [])
    index = data.get("current_index", 0)

    if not forms or index >= len(forms):
        return

    target_form_id = forms[index]["id"]
    
    target_form = await formAccessor.get_form_by_user_id(target_form_id)
    
    success, is_match = await formAccessor.add_like(message.from_user.id, target_form.id)

    if is_match:
        target_user = await userAccessor.get_user(user_id=target_form_id)
        my_form = await formAccessor.get_form_by_user_id(message.from_user.id)
        my_user = await userAccessor.get_user(user_id=message.from_user.id)

        await send_form_message(message, target_form, username=target_user.username)

        try:
            match_caption = build_form_text(my_form)
            
            if my_form.images:
                media = [InputMediaPhoto(media=img.file_id, caption=match_caption if i == 0 else "", parse_mode="HTML") 
                         for i, img in enumerate(my_form.images[:3])]
                await message.bot.send_media_group(chat_id=target_form_id, media=media)

                await message.bot.send_message(chat_id=target_form_id, text=f"🎉 <b>Это взаимно!</b>\n@{my_user.username} ждет твоего сообщения.", 
                                    reply_markup=build_reply_keyboard(build_main_keyboard(), adjust=[2, 2]))
            else:
                await message.bot.send_message(chat_id=target_form_id, text=match_caption, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error notifying target: {e}")

    else:
        try:
            await message.bot.send_message(
                chat_id=target_form_id,
                text="❤️ Твоя анкета кому-то понравилась!",
                reply_markup=build_reply_keyboard([{"text": LikeButtons.SEE_FORM.value}, {"text" : LikeButtons.SNOOZE_FORM.value}], adjust=[2])
            )
        except Exception:
            pass

    await state.update_data(current_index=index + 1)
    await show_next_form(message, state)

@router.message(F.text == LikeButtons.SEE_FORM.value)
async def see_form_handler(message: Message, state: FSMContext):
    incoming_forms = await formAccessor.get_sympathy_forms(message.from_user.id)
    
    if not incoming_forms:
        await message.answer("Упс! Попробуй обычный поиск!", 
                             reply_markup=build_reply_keyboard(build_main_keyboard(), adjust=[2,2]))
        return

    forms_data = [{"id": f.user_id, "dist": None} for f in incoming_forms]
    
    await state.set_state(SearchState.viewing)
    await state.update_data(forms=forms_data, current_index=0, seen_ids=[])
    
    await message.answer("Давай посмотрим, кому ты нравишься!")
    
    await show_next_form(message, state)

@router.message(F.text == LikeButtons.SNOOZE_FORM.value)
async def snooze_form_handler(message: Message, state: FSMContext):
    await message.answer("Хорошо, загляни позже! Анкета будет ждать тебя в симпатиях.", 
                         reply_markup=build_reply_keyboard(build_main_keyboard(), adjust=[2,2]))
    await state.clear()

@router.message(SearchState.viewing, F.text == BotButtons.SKIP.value)
async def search_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    index = data.get("current_index")

    await state.update_data(current_index=index + 1)
    await show_next_form(message, state)

@router.message(SearchState.viewing, F.text == BotButtons.BACK.value)
async def back_button_search_handler(message: Message, state: FSMContext):
    form = await formAccessor.get_form_by_user_id(message.from_user.id)
    await send_form_message(message, form)

    await state.clear()

@router.message(SearchState.viewing)
async def show_next_form(message: Message, state: FSMContext):
    data = await state.get_data()

    last_view_time = data.get("last_view_time")
    current_time = time.time()
    two_hours_in_seconds = 7200

    if last_view_time and (current_time - last_view_time > two_hours_in_seconds):
        await state.update_data(seen_ids=[], last_view_time=current_time)
        seen_ids = []
        logger.info(f"Список seen_ids для пользователя {message.from_user.id} обнулен по истечении 2 часов.")
    else:
        seen_ids = data.get("seen_ids", [])

    forms = data.get("forms", [])
    index = data.get("current_index", 0)

    if index >= len(forms):
        my_form = await formAccessor.get_form_by_user_id(message.from_user.id)
        if not my_form: return

        gender_search = my_form.search_settings.gender_search
        target = gender_search if gender_search != InlineButtons.NO_GENDER_SEARCH.text_data else None

        lat, lon = (my_form.latitude, my_form.longitude) if my_form.search_settings.geo_search else (None, None)

        logger.info(f"seen_ids: {seen_ids}")

        new_forms = await formAccessor.get_search_forms(user_id=message.from_user.id,
        target_gender=target, lat=lat, lon=lon, exclude_ids=seen_ids)

        if not new_forms:
            await message.answer("Пока это все в округе!\n\nПриходи позже", reply_markup=build_reply_keyboard([{"text": BotButtons.BACK.value}]))
            # await back_button_search_handler(message, state)
            return
        
        forms = [{"id": f.user_id, "dist": f.distance_km} for f in new_forms]
        index = 0
        await state.update_data(forms=forms, current_index=index)

    current_item = forms[index]
    target_form = await formAccessor.get_form_by_user_id(current_item["id"])

    target_form.distance_km = current_item["dist"]

    seen_ids.append(target_form.id)
    await state.update_data(seen_ids=seen_ids, last_view_time=time.time())

    await send_search_form_message(message=message, form=target_form)

# ----------- SETTINGS -----------

@router.message(F.text == BotButtons.SEARCH_SETTINGS.value)
async def search_settings_handler(message: Message, state: FSMContext):
    await state.set_state(SearchState.settings)

    form = await formAccessor.get_form_by_user_id(message.from_user.id)
    await state.update_data(gender_search=form.search_settings.gender_search, geo_search=form.search_settings.geo_search)

    await message.answer("Что ты хочешь настроить?\n\n"\
    f"Гендер: {form.search_settings.gender_search}\nПоиск по городу: {'Вкл.' if form.search_settings.geo_search == True else 'Выкл.'}", reply_markup=build_inline_keyboard(
        [{"text" : InlineButtons.GENDER_SEARCH.text, "callback_data" : InlineButtons.GENDER_SEARCH.callback_data},
         {"text": InlineButtons.LOCATION_SEARCH.text, "callback_data" : InlineButtons.LOCATION_SEARCH.callback_data},
         {"text": InlineButtons.DONE.text, "callback_data": InlineButtons.DONE.callback_data}], adjust=[1,1,1]
    ))

@router.callback_query(F.data == InlineButtons.DONE.callback_data)
async def done_settings_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_gender_search = data.get("gender_search")
    state_geo_search = data.get("geo_search")

    await callback.answer("Настройки сохранены!")
    form = await formAccessor.get_form_by_user_id(callback.from_user.id)
    if form and form.search_settings:
        gender_search = form.search_settings.gender_search
        geo_search = form.search_settings.geo_search

    update_fields = {}
    if gender_search != state_gender_search:
        update_fields["gender_search"] = state_gender_search

    if geo_search != state_geo_search:
        update_fields["geo_search"] = state_geo_search

    await formAccessor.update_form(callback.from_user.id, **update_fields)

    await callback.message.delete()

    await state.clear()

@router.callback_query(SearchState.gender_settings, F.data == InlineButtons.BACK.callback_data)
async def back_settings_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.settings)
    data = await state.get_data()

    await show_edit_keyboard(callback, state)

@router.callback_query(F.data == InlineButtons.GENDER_SEARCH.callback_data)
async def gender_settings_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.gender_settings)
    data = await state.get_data()

    keyboard = [{"text": btn.text, "callback_data" : btn.callback_data} for btn in (InlineButtons.FEMALE_GENDER, 
    InlineButtons.MALE_GENDER, InlineButtons.ANOTHER_GENDER, InlineButtons.NO_GENDER_SEARCH, InlineButtons.BACK)]
    markup = build_inline_keyboard(keyboard, adjust=[3, 1, 1])
    form = await formAccessor.get_form_by_user_id(callback.from_user.id)
    gender_search = data.get("gender_search", form.search_settings.gender_search)  

    await callback.message.edit_text(text=f"Изменение поиска по гендру\n\nТекущий режим: {gender_search}", reply_markup=markup)

@router.callback_query(SearchState.gender_settings, F.data.in_([InlineButtons.FEMALE_GENDER.callback_data, InlineButtons.MALE_GENDER.callback_data, InlineButtons.ANOTHER_GENDER.callback_data, InlineButtons.NO_GENDER_SEARCH.callback_data]))
async def gender_search_callback(callback: CallbackQuery, state: FSMContext):
    text = InlineButtons.NO_GENDER_SEARCH.text

    for btn in [InlineButtons.FEMALE_GENDER, InlineButtons.MALE_GENDER, InlineButtons.ANOTHER_GENDER, InlineButtons.NO_GENDER_SEARCH]:
        if btn.callback_data == callback.data:
            text = btn.text
            text_data = btn.text_data

    await callback.answer(f"Поиск: {text}")

    await state.update_data(gender_search=text_data)
    await show_edit_keyboard(callback, state)
    
@router.callback_query(SearchState.settings, F.data == InlineButtons.LOCATION_SEARCH.callback_data)
async def switch_geo_search_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    status = not data.get("geo_search")
    
    callback.answer(f"Поиск по локации: {'Вкл.' if status else 'Выкл.'}")

    await state.update_data(geo_search=status)
    await show_edit_keyboard(callback, state)

async def show_edit_keyboard(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    gender_search = data.get("gender_search")
    geo_search = data.get("geo_search")

    await callback.message.edit_text("Что ты хочешь настроить?\n\n"\
    f"Текущие настройки:\nГендер: {gender_search}\nПоиск по городу: {'Вкл.' if geo_search == True else 'Выкл.'}", reply_markup=build_inline_keyboard(
        [{"text" : InlineButtons.GENDER_SEARCH.text, "callback_data" : InlineButtons.GENDER_SEARCH.callback_data},
         {"text": InlineButtons.LOCATION_SEARCH.text, "callback_data" : InlineButtons.LOCATION_SEARCH.callback_data},
         {"text": InlineButtons.DONE.text, "callback_data": InlineButtons.DONE.callback_data}], adjust=[1,1,1]
    ))