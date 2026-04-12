from enum import Enum
import logging

from aiogram.types import InputMediaPhoto, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

logger = logging.getLogger(__name__)

class BotButtons(Enum):
    SEARCH = "Поиск"
    SYMPATHIES = "Симпатии"
    EDIT_FORM = "Изменить анкету"
    DISABLE_FORM = "Улететь из гнезда"
    ENABLE_FORM = "Подлететь к гнезду"
    SEARCH_SETTINGS = "Настроить поиск"

    SET_CURR = "Оставить прежним"

    LIKE = "❤️ Нравится"
    SKIP = "👎 Пропустить"
    BACK = "⛔️ Назад"

class InlineButtons(Enum):
    BACK = {"text" : "Назад", "callback_data": "cb_back"}
    DONE = {"text" : "Применить", "callback_data": "cb_done"}
    GENDER_SEARCH = {"text" : "Поиск по гендеру", "callback_data" : "genderSearch"}
    LOCATION_SEARCH = {"text" : "Поиск по городу", "callback_data" : "citySearch"}

    MALE_GENDER = {"text" : "Парни", "callback_data" : "gs_maleSearch"}
    FEMALE_GENDER = {"text" : "Девушки", "callback_data" : "gs_femaleSearch"}
    ANOTHER_GENDER = {"text" : "Другое", "callback_data" : "gs_anotherSearch"}
    NO_GENDER_SEARCH = {"text" : "Без разницы", "callback_data" : "gs_noMatter"}

    @property
    def text(self):
        texts = {
            InlineButtons.GENDER_SEARCH: "Поиск по гендеру",
            InlineButtons.LOCATION_SEARCH: "Поиск по городу",
            InlineButtons.MALE_GENDER: "Парни",
            InlineButtons.FEMALE_GENDER: "Девушки",
            InlineButtons.ANOTHER_GENDER: "Другое",
            InlineButtons.NO_GENDER_SEARCH: "Без разницы",
            InlineButtons.BACK: "Назад",
            InlineButtons.DONE: "Применить"
        }
        return texts[self]
    
    @property
    def callback_data(self):
        data = {
            InlineButtons.GENDER_SEARCH: "genderSearch",
            InlineButtons.LOCATION_SEARCH: "citySearch",
            InlineButtons.MALE_GENDER: "gs_maleSearch",
            InlineButtons.FEMALE_GENDER: "gs_femaleSearch",
            InlineButtons.ANOTHER_GENDER: "gs_anotherSearch",
            InlineButtons.NO_GENDER_SEARCH: "gs_noMatter",
            InlineButtons.BACK: "cb_back",
            InlineButtons.DONE: "cb_done"
        }
        return data[self]
    
    @property
    def text_data(self):
        data = {
            InlineButtons.MALE_GENDER: "Парень",
            InlineButtons.FEMALE_GENDER: "Девушка",
            InlineButtons.ANOTHER_GENDER: "Другое",
            InlineButtons.NO_GENDER_SEARCH: None,
        }

        return data[self]



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

    dist_str = ""
    if hasattr(form, "distance_km") and form.distance_km is not None:
        logger.info(f"distance_km: {form.distance_km}")
        if form.distance_km < 1:
            dist_str = f"📍 Менее 1 км"
        else:
            dist_str = f"📍 В {form.distance_km} км от тебя"

    return f"<b>{name}</b> – {gender} {age} {city}\n{dist_str}\n\n{description}"

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

async def send_search_form_message(message, form):
    if not form.images:
        return await message.answer(build_form_text(form))
    
    media = []

    for i, img in enumerate(form.images):
        if i == 0:
            media.append(InputMediaPhoto(media=img.file_id, caption=build_form_text(form), parse_mode="HTML"))
        else:
            media.append(InputMediaPhoto(media=img.file_id))

    keyboard = build_search_keyboard()
    await message.answer("Нашли птичку:", reply_markup=build_reply_keyboard(
        keyboard,
        adjust=[2, 2],))
    return await message.answer_media_group(media=media[:3])

def build_main_keyboard():
    return [{"text": BotButtons.SEARCH.value},{"text": BotButtons.SYMPATHIES.value},{"text": BotButtons.EDIT_FORM.value},{"text": BotButtons.SEARCH_SETTINGS.value}, {"text": BotButtons.DISABLE_FORM.value}]

def build_edit_keyboard():
    return [{"text": BotButtons.SET_CURR.value}]

def build_search_keyboard():
    return [{"text": BotButtons.LIKE.value}, {"text": BotButtons.SKIP.value}, {"text": BotButtons.BACK.value}]

