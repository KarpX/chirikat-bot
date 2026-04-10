from enum import Enum

from aiogram.types import InputMediaPhoto, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

class BotButtons(Enum):
    SEARCH = "Поиск"
    SYMPATHIES = "Симпатии"
    EDIT_FORM = "Изменить анкету"
    DELETE_FORM = "Улететь из гнезда"


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
    return f"<b>{form.name}</b> – {form.gender.lower()} {form.age} {f', {form.city}' if form.city is not None else ''}\n\n{form.description}"

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
        [{"text": BotButtons.SEARCH.value},{"text": BotButtons.SYMPATHIES.value},{"text": BotButtons.EDIT_FORM.value}, {"text": BotButtons.DELETE_FORM.value}],
        adjust=[2, 2],))
    return await message.answer_media_group(media=media[:3])