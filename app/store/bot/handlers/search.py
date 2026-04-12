import logging

from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.forms.accessor import formAccessor
from app.store.bot.builders import BotButtons, InlineButtons, build_inline_keyboard, build_reply_keyboard, send_form_message, send_search_form_message
from app.store.bot.handlers.form import Gender

logger = logging.getLogger(__name__)

router = Router()

class SearchState(StatesGroup):
    viewing = State()
    settings = State()
    gender_settings = State()

@router.message(F.text == BotButtons.SEARCH.value)
async def search_handler(message: Message, state: FSMContext):
    await message.answer("Ищем для тебя самых лучших птичек!")
    await state.set_state(SearchState.viewing)
    await show_next_form(message, state)

@router.message(SearchState.viewing, F.text == BotButtons.LIKE.value)
async def searh_handler(message: Message, state: FSMContext):
    await message.answer("Вам понравилась анкета!")

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
    forms = data.get("forms", [])
    index = data.get("current_index", 0)
    seen_ids = data.get("seen_ids", [])

    if index >= len(forms):
        my_form = await formAccessor.get_form_by_user_id(message.from_user.id)
        gender_search = my_form.search_settings.gender_search
        target = gender_search if gender_search != InlineButtons.NO_GENDER_SEARCH.text else None

        lat = None
        lon = None
        if my_form.search_settings.geo_search:
            lat = my_form.latitude
            lon = my_form.longitude

        new_forms = await formAccessor.get_search_forms(user_id=message.from_user.id,
        target_gender=target, lat=lat, lon=lon, exclude_ids=seen_ids)

        if not new_forms:
            await message.answer("Пока это все птички в округе!\n\nЗалетай позже", reply_markup=build_reply_keyboard([{"text": BotButtons.BACK.value}]))
            await back_button_search_handler(message, state)
            return
        
        forms = [f.user_id for f in new_forms]
        index = 0
        await state.update_data(forms=forms, current_index=index)

    target_form = await formAccessor.get_form_by_user_id(forms[index])

    seen_ids.append(target_form.id)
    await state.update_data(seen_ids=seen_ids)

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

    for btn in [InlineButtons.FEMALE_GENDER, InlineButtons.MALE_GENDER, InlineButtons.ANOTHER_GENDER]:
        if btn.callback_data == callback.data:
            text = btn.text

    await callback.answer(f"Поиск: {text}")

    keyboard = [{"text": btn.text, "callback_data" : btn.callback_data} for btn in (InlineButtons.FEMALE_GENDER, 
    InlineButtons.MALE_GENDER, InlineButtons.ANOTHER_GENDER, InlineButtons.NO_GENDER_SEARCH, InlineButtons.BACK)]

    await state.update_data(gender_search=text)
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
    f"Гендер: {gender_search}\nПоиск по городу: {'Вкл.' if geo_search == True else 'Выкл.'}", reply_markup=build_inline_keyboard(
        [{"text" : InlineButtons.GENDER_SEARCH.text, "callback_data" : InlineButtons.GENDER_SEARCH.callback_data},
         {"text": InlineButtons.LOCATION_SEARCH.text, "callback_data" : InlineButtons.LOCATION_SEARCH.callback_data},
         {"text": InlineButtons.DONE.text, "callback_data": InlineButtons.DONE.callback_data}], adjust=[1,1,1]
    ))