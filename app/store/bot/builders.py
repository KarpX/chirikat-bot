from enum import Enum

from aiogram.types import InputMediaPhoto, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

class BotButtons(Enum):
    SEARCH = "Поиск"
    SYMPATHIES = "Симпатии"
    EDIT_FORM = "Изменить анкету"
    DISABLE_FORM = "Улететь из гнезда"
    ENABLE_FORM = "Подлететь к гнезду"

    SET_CURR = "Оставить прежним"


def build_inline_keyboard(list_of_buttons, adjust: list[int] = None):
    inline_builder = InlineKeyboardBuilder()
    for button in list_of_buttons:
        inline_builder.button(text=button["text"], callback_data=button["callback_data"])

    if adjust is not None:
        inline_builder.adjust(*adjust)

    return inline_builder.as_markup()


def build_reply_keyboard(list_of_buttons, adjust: list[int] = None, one_time_keyboard: bool = False):
    builder = ReplyKeyboardBuilder()
    for button in list_of_buttons:
        builder.button(text=button["text"])

    if adjust is not None:
        builder.adjust(*adjust)

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=one_time_keyboard)


def build_reply_keyboard_with_location(list_of_buttons, adjust: list[int] = None, one_time_keyboard: bool = False):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📍 Отправить местоположение", request_location=True)
    for button in list_of_buttons:
        builder.button(text=button["text"])
    
    if adjust is not None:
        builder.adjust(*adjust)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=one_time_keyboard)


def remove_reply_keyboard():
    return ReplyKeyboardRemove()


def build_form_text(form):
    name = form.name
    gender = form.gender.lower()
    age = form.age
    city = f', {form.city}' if form.city is not None else ''
    description = "" if form.description is None else form.description
    return f"<b>{name}</b> – {gender} {age} {city}\n\n{description}"

async def send_form_message(message, form):
    if not form.images:
        return await message.answer(build_form_text(form))
    
    media = []

    for i, img in enumerate(form.images):
        if i == 0:
            media.append(InputMediaPhoto(media=img.file_id, caption=build_form_text(form), parse_mode="HTML"))
        else:
            media.append(InputMediaPhoto(media=img.file_id))


    await message.answer("Вот твоя анкета:", reply_markup=build_reply_keyboard(
        build_main_keyboard(),
        adjust=[2, 2],))
    return await message.answer_media_group(media=media[:3])

def build_main_keyboard():
    return [{"text": BotButtons.SEARCH.value},{"text": BotButtons.SYMPATHIES.value},{"text": BotButtons.EDIT_FORM.value}, {"text": BotButtons.DISABLE_FORM.value}]

def build_edit_keyboard():
    return [{"text": BotButtons.SET_CURR.value}]

