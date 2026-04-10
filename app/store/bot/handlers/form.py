from enum import Enum

from geopy.geocoders import Nominatim

from aiogram.fsm.state import State, StatesGroup
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.forms.accessor import formAccessor, formImageAccessor

from app.store.bot.builders import BotButtons, build_inline_keyboard, build_reply_keyboard, build_reply_keyboard_with_location, remove_reply_keyboard, send_form_message

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

class EditFormButtons(Enum):
    IMAGE = "Фото"
    DESCRIPTION = "О себе"
    ALL = "Заполнить заново"

router = Router()

geolocator = Nominatim(user_agent="my_dating_bot")


@router.message(FormState.city, F.location)
async def handle_location(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    
    try:
        location = geolocator.reverse(f"{lat}, {lon}", language="ru")
        address = location.raw.get('address', {})
        city_name = address.get('city') or address.get('town') or address.get('village') or "Неизвестное гнёздышко"
    except Exception:
        await message.answer(f"Попробуй ещё раз!")
        return

    await state.update_data(city=city_name, latitude=lat, longitude=lon)
    
    await state.set_state(FormState.gender)
    await message.answer(f"Твой город: <b>{city_name}</b> \n\nТеперь выбери пол", 
                         reply_markup=build_reply_keyboard(
                             [{"text": Gender.MALE.value}, {"text": Gender.FEMALE.value}, {"text": Gender.OTHER.value}], 
                             adjust=[3]
                         ), parse_mode="HTML")


@router.message(FormState.city, F.text)
async def form_city_text(message: Message, state: FSMContext):   
    if message.text.strip().lower() == "пропустить":
        await state.update_data(city="") 
        await state.set_state(FormState.gender)
        await message.answer(f"Теперь выбери пол:", 
                         reply_markup=build_reply_keyboard(
                             [{"text": Gender.MALE.value}, {"text": Gender.FEMALE.value}, {"text": Gender.OTHER.value}], 
                             adjust=[3]
                         ))
        return
        
    return await message.answer("Отправь своё местоположение с помощью кнопки, чтобы указать город, или пропусти!")


@router.message(FormState.name)
async def form_handler(message, state: FSMContext):
    if message.text.strip() == "":
        await message.answer("Пожалуйста, введи корректное имя")
        return
    
    if len(message.text.strip()) > 20:
        await message.answer("Какое прекрасное длинное имя!\n\n<i>Мы все обзавидуемся такой крутизне. Давай покороче</i>")
    
    await state.update_data(name=message.text.strip())

    await state.set_state(FormState.age)
    await message.answer("Сколько тебе лет?")


@router.message(FormState.age)
async def form_handler(message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи корректный возраст")
        return
    
    if int(message.text) < 16 or int(message.text) > 110:
        await message.answer("Крылышки слишком слабы, чтобы летать в таком возрасте!")
        return
    
    await state.update_data(age=int(message.text))

    await state.set_state(FormState.city)
    await message.answer("Из какого ты гнёздышка?", reply_markup=build_reply_keyboard_with_location([{"text" : "Пропустить"}], one_time_keyboard=True))


# @router.message(FormState.city)
# async def form_handler(message, state: FSMContext):    
#     await state.update_data(city=message.text)

#     await state.set_state(FormState.gender)
#     await message.answer("Какого ты пола?", reply_markup=build_reply_keyboard(
#         [{"text": Gender.MALE.value}, {"text": Gender.FEMALE.value}, {"text": Gender.OTHER.value}], 
#         adjust=[3], 
#         one_time_keyboard=True
#         ))

@router.message(FormState.gender)
async def form_handler(message, state: FSMContext):
    if message.text.strip().lower() not in [gender.value.lower() for gender in Gender]:
        await message.answer("Пожалуйста, введи корректный пол")
        return
    
    await state.update_data(gender=message.text.strip())

    await state.set_state(FormState.image)
    await message.answer("Покажи себя! \n\n<i>Оперение птичек может много о них рассказать</i>", reply_markup=remove_reply_keyboard(), parse_mode="HTML")


@router.message(FormState.image, F.photo)
async def form_handler(message, state: FSMContext):
    data = await state.get_data()

    images = data.get("image", [])

    images.append(message.photo[-1].file_id)
    await state.update_data(image=images)

    if len(images) < 3:
        await message.answer(
            f"Фото добавлено ({len(images)}/3). \n\nПоделишься ещё красотой оперения или хватит?",
            reply_markup=build_reply_keyboard([{"text":"Хватит!"}])
        )
    else:
        await process_images_done(message, state)
        # await state.set_state(FormState.description)
        # await message.answer("Отлично выглядишь! \n\nА теперь начирикай немного о себе", reply_markup=remove_reply_keyboard())

@router.message(FormState.image, F.text == "Хватит!")
async def form_handler(message, state: FSMContext):
    data = await state.get_data()
    if not data.get("image"):
        await message.answer("Пришли хотя бы одно фото")
        return
    

    await process_images_done(message, state)
    # await state.set_state(FormState.description)
    # await message.answer("Отлично выглядишь! \n\nА теперь начирикай немного о себе", reply_markup=remove_reply_keyboard())


@router.message(FormState.description)
async def form_handler(message: Message, state: FSMContext):    
    await state.update_data(description=message.text)
    data = await state.get_data()
    user_id = message.from_user.id

    existing_form = await formAccessor.get_form_by_user_id(user_id)

    if existing_form:
        new_form = await formAccessor.update_form(
            user_id=user_id,
            name=data.get('name', existing_form.name),
            age=data.get('age', existing_form.age),
            city=data.get('city', existing_form.city),
            gender=data.get('gender', existing_form.gender),
            description=data['description']
        )
        if "image" in data:
            await formImageAccessor.delete_images_by_form_id(new_form.id)
            for file_id in data['image']:
                await formImageAccessor.create_form_image(form_id=new_form.id, file_id=file_id)
    else:
        new_form = await formAccessor.create_form(
            user_id=user_id, 
            name=data['name'], 
            age=data['age'], 
            city=data['city'] if data['city'].strip() != "" else None, 
            gender=data['gender'], 
            description=data['description'],
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        for file_id in data['image']:
            await formImageAccessor.create_form_image(form_id=new_form.id, file_id=file_id)

    full_form = await formAccessor.get_form_by_user_id(user_id)
    await message.answer("Готово! Твоя обновленная анкета:")
    await send_form_message(message, full_form)
    await state.clear()


async def process_images_done(message: Message, state: FSMContext):
    data = await state.get_data()
    
    if data.get("edit_type") == "image":
        form = await formAccessor.get_form_by_user_id(message.from_user.id)
        await formImageAccessor.delete_images_by_form_id(form.id)
        
        for file_id in data['image']:
            await formImageAccessor.create_form_image(form_id=form.id, file_id=file_id)
        
        await message.answer("Фотографии обновлены!")
        full_form = await formAccessor.get_form_by_user_id(message.from_user.id)
        await send_form_message(message, full_form)
        await state.clear()
    else:
        await state.set_state(FormState.description)
        await message.answer("Отлично выглядишь! \n\nА теперь начирикай немного о себе", reply_markup=remove_reply_keyboard())


@router.callback_query(F.data == "EditAll")
async def edit_all_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Давай заполним всё заново! Как тебя зовут?")
    await state.set_state(FormState.name)
    await callback.answer()


@router.callback_query(F.data == "EditDescription")
async def edit_desc_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FormState.description)

    await state.update_data(is_editing=True) 
    await callback.message.answer("Начирикай новое описание о себе")
    await callback.answer()


@router.callback_query(F.data == "EditImage")
async def edit_image_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FormState.image)

    await state.update_data(image=[], is_editing=True, edit_type="image") 
    await callback.message.answer("Пришли от 1 до 3 новых фотографий")
    await callback.answer()


@router.message(F.text == BotButtons.EDIT_FORM.value)
async def edit_form_handler(message):
    await message.answer("Что ты хочешь изменить?", reply_markup=build_inline_keyboard(
        [{"text": EditFormButtons.IMAGE.value, "callback_data" : "EditImage"}, 
         {"text": EditFormButtons.DESCRIPTION.value, "callback_data" : "EditDescription"}, 
         {"text": EditFormButtons.ALL.value, "callback_data": "EditAll"}],
        adjust=[2, 1]
        ))