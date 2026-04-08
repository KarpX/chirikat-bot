from enum import Enum

from aiogram.fsm.state import State, StatesGroup
from aiogram import Router
from aiogram.fsm.context import FSMContext

from app.store.bot.builders import build_reply_keyboard

class FormState(StatesGroup):
    name = State()
    age = State()
    city = State()
    gender = State()
    image = State()
    description = State()

class Gender(Enum):
    MALE = "Парень"
    FEMALE = "Девушка"
    OTHER = "Другое"

router = Router()


@router.message(FormState.name)
async def form_handler(message, state: FSMContext):
    if message.text.strip() == "":
        await message.answer("Пожалуйста, введи корректное имя.")
        return
    
    await state.update_data(name=message.text)

    await state.set_state(FormState.age)
    await message.answer("Сколько тебе лет?")


@router.message(FormState.age)
async def form_handler(message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи корректный возраст.")
        return
    
    await state.update_data(age=int(message.text))

    await state.set_state(FormState.city)
    await message.answer("Из какого ты города?")


@router.message(FormState.city)
async def form_handler(message, state: FSMContext):
    if message.text.strip() == "":
        await message.answer("Пожалуйста, введи корректный город.")
        return
    
    await state.update_data(city=message.text)

    await state.set_state(FormState.gender)
    await message.answer("Какого ты пола?", reply_markup=build_reply_keyboard([{"text": Gender.MALE.value}, {"text": Gender.FEMALE.value}, {"text": Gender.OTHER.value}], adjust=[3]))


@router.message(FormState.gender)
async def form_handler(message, state: FSMContext):
    if message.text.strip().lower() not in [gender.value.lower() for gender in Gender]:
        await message.answer("Пожалуйста, введи корректный пол.")
        return
    
    await state.update_data(gender=message.text.strip())

    await state.set_state(FormState.image)
    await message.answer("Пришли свою фотографию")


@router.message(FormState.image)
async def form_handler(message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, пришли фотографию", reply_markup=None)
        return
    
    await state.update_data(image=message.photo[-1].file_id)

    await state.set_state(FormState.description)
    await message.answer("Расскажи немного о себе")


@router.message(FormState.description)
async def form_handler(message, state: FSMContext):    
    await state.update_data(description=message.text)

    data = await state.get_data()
    await message.answer_photo(photo=data['image'], caption=f"Анкета успешно заполнена!\n\nИмя: {data['name']}\nВозраст: {data['age']}\nГород: {data['city']}\nПол: {data['gender']}\nОписание: {data['description']}")