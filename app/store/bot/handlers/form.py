from enum import Enum
import logging

from geopy.geocoders import Nominatim

from aiogram.fsm.state import State, StatesGroup
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.forms.accessor import formAccessor, formImageAccessor

from app.store.bot.builders import BotButtons, build_edit_keyboard, build_inline_keyboard, build_main_keyboard, build_reply_keyboard, build_reply_keyboard_with_location, remove_reply_keyboard, send_form_message

logger = logging.getLogger(__name__)

class FormState(StatesGroup):
    name = State()
    age = State()
    city = State()
    gender = State()
    image = State()
    description = State()


class ProfileState(StatesGroup):
    confirm_disable = State()

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
        await state.update_data(city=None, latitude=None, longitude=None) 
        await state.set_state(FormState.gender)
        await message.answer(f"Теперь выбери пол:", 
                         reply_markup=build_reply_keyboard(
                             [{"text": Gender.MALE.value}, {"text": Gender.FEMALE.value}, {"text": Gender.OTHER.value}], 
                             adjust=[3]
                         ))
        return
    
    elif message.text == BotButtons.SET_CURR.value:
        existing_form = await formAccessor.get_form_by_user_id(message.from_user.id)
        await state.update_data(city=existing_form.city, latitude=existing_form.latitude, longitude=existing_form.longitude) 
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
    text = message.text.strip()
    
    if text == BotButtons.SET_CURR.value:
        existing_form = await formAccessor.get_form_by_user_id(message.from_user.id)
        text = existing_form.name
    
    if len(text) > 20:
        await message.answer("Какое прекрасное длинное имя!\n\n<i>Мы все обзавидуемся такой крутизне. Давай покороче</i>")
    
    await state.update_data(name=text)

    await state.set_state(FormState.age)
    data = await state.get_data()
    is_editing = data.get("is_editing")
    keyboard = []
    if is_editing:
        keyboard += build_edit_keyboard()
    await message.answer("Сколько тебе лет?", reply_markup=build_reply_keyboard(keyboard))


@router.message(FormState.age)
async def form_handler(message, state: FSMContext):    
    text = message.text
    
    if text == BotButtons.SET_CURR.value:
        existing_form = await formAccessor.get_form_by_user_id(message.from_user.id)
        text = existing_form.age

    if not str(text).isdigit():
        await message.answer("Пожалуйста, введи корректный возраст")
        return
    
    if int(text) < 16 or int(text) > 110:
        await message.answer("Крылышки слишком слабы, чтобы летать в таком возрасте!")
        return
    
    await state.update_data(age=int(text))
    await state.set_state(FormState.city)
    data = await state.get_data()
    is_editing = data.get("is_editing")
    keyboard = [{"text" : "Пропустить"}]
    if is_editing:
        keyboard += build_edit_keyboard()

    await message.answer("Из какого ты гнёздышка?", reply_markup=build_reply_keyboard_with_location(keyboard, adjust=[2, 1], one_time_keyboard=True))


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
    data = await state.get_data()
    is_editing = data.get("is_editing")
    kb = remove_reply_keyboard()
    keyboard = []
    if is_editing:
        keyboard += build_edit_keyboard()
        kb = build_reply_keyboard(keyboard)

    await message.answer("Покажи себя! \n\n<i>Оперение птичек может много о них рассказать</i>", reply_markup=kb, parse_mode="HTML")


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

@router.message(FormState.image, F.text == "Хватит!")
async def form_handler(message, state: FSMContext):
    data = await state.get_data()
    if not data.get("image"):
        await message.answer("Пришли хотя бы одно фото")
        return
    

    await process_images_done(message, state)

@router.message(FormState.image, F.text == BotButtons.SET_CURR.value)
async def form_handler(message, state: FSMContext):
    data = await state.get_data()
    
    if data.get("is_editing") and data.get("edit_type") == "image":
        logger.info("here")
        full_form = await formAccessor.get_form_by_user_id(message.from_user.id)
        await send_form_message(message, full_form)
        await state.clear()
    else:
        await state.update_data(image=None) 
        
        await state.set_state(FormState.description)
        await message.answer(
            "Теперь начирикай что-нибудь о себе", 
            reply_markup=build_reply_keyboard([
                {"text" : "Оставить поле пустым"},
                {"text" : BotButtons.SET_CURR.value}
            ])
        )


@router.message(FormState.description)
async def form_handler(message: Message, state: FSMContext):
    if message.text == BotButtons.SET_CURR.value:
        existing_form = await formAccessor.get_form_by_user_id(message.from_user.id)
        await state.update_data(description=existing_form.description)
    else:
        await state.update_data(description=message.text)
    
    data = await state.get_data()
    user_id = message.from_user.id

    existing_form = await formAccessor.get_form_by_user_id(user_id)

    destription = data['description']
    if destription == "Оставить поле пустым":
        destription = None

    if existing_form:
        update_fields = {
            "name": data.get('name', existing_form.name),
            "age": data.get('age', existing_form.age),
            "city": data.get('city'),
            "gender": data.get('gender', existing_form.gender),
            "description": destription,
            "geo_search": False
        }

        if 'latitude' in data:
            update_fields["latitude"] = data.get('latitude')
            update_fields["longitude"] = data.get('longitude') 
        
        if data.get('city') is not None:
            update_fields["geo_search"] = True

        logger.info(f"update_fields: {update_fields}")

        new_form = await formAccessor.update_form(user_id=user_id, **update_fields)

        if "image" in data and data['image'] is not None:
            await formImageAccessor.delete_images_by_form_id(new_form.id)
            for file_id in data['image']:
                await formImageAccessor.create_form_image(form_id=new_form.id, file_id=file_id)
    else:
        new_form = await formAccessor.create_form(
            user_id=user_id, 
            name=data['name'], 
            age=data['age'], 
            city=data['city'], 
            gender=data['gender'], 
            description=destription,
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        for file_id in data['image']:
            await formImageAccessor.create_form_image(form_id=new_form.id, file_id=file_id)

    full_form = await formAccessor.get_form_by_user_id(user_id)
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
        is_editing = data.get("is_editing")
        keyboard = [{"text" : "Оставить поле пустым"}]
        if is_editing:
            keyboard += build_edit_keyboard()
        await message.answer("Отлично выглядишь! \n\nА теперь начирикай немного о себе", 
                             reply_markup=build_reply_keyboard(keyboard))


@router.callback_query(F.data == "EditAll")
async def edit_all_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await state.update_data(is_editing=True)

    await callback.message.delete()
    keyboard = build_edit_keyboard()

    await callback.message.answer("Давай заполним всё заново! \nКак тебя зовут?", reply_markup=build_reply_keyboard(keyboard))
    await state.set_state(FormState.name)
    await callback.answer()


@router.callback_query(F.data == "EditDescription")
async def edit_desc_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FormState.description)

    await callback.message.delete() 

    await state.update_data(is_editing=True) 
    keyboard = build_edit_keyboard()
    await callback.message.answer("Начирикай новое описание о себе", reply_markup=build_reply_keyboard(keyboard))
    await callback.answer()


@router.callback_query(F.data == "EditImage")
async def edit_image_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FormState.image)

    await callback.message.delete() 

    await state.update_data(image=[], is_editing=True, edit_type="image") 
    keyboard = build_edit_keyboard()
    await callback.message.answer("Пришли от 1 до 3 новых фотографий", reply_markup=build_reply_keyboard(keyboard))
    await callback.answer()


@router.message(F.text == BotButtons.EDIT_FORM.value)
async def edit_form_handler(message):
    await message.answer("Что ты хочешь изменить?", reply_markup=build_inline_keyboard(
        [{"text": EditFormButtons.IMAGE.value, "callback_data" : "EditImage"}, 
         {"text": EditFormButtons.DESCRIPTION.value, "callback_data" : "EditDescription"}, 
         {"text": EditFormButtons.ALL.value, "callback_data": "EditAll"}],
        adjust=[2, 1]
        ))
    
@router.message(F.text == BotButtons.DISABLE_FORM.value)
async def delete_form_handler(message: Message, state: FSMContext):
    await state.set_state(ProfileState.confirm_disable)

    await message.answer("Ты точно хочешь покинуть гнездо?\n\n<i>Мы больше не будем предлагать тебя другим птичкам, но ты сможешь вернуться!</i>", reply_markup=build_reply_keyboard(
        [{"text" : "Нет, остаюсь!"}, {"text" : "Уверен"}]), parse_mode="HTML")
    
@router.message(ProfileState.confirm_disable, F.text == "Нет, остаюсь!")
async def delete_form_handler(message: Message, state: FSMContext):
    await state.clear()
    keyboard = build_main_keyboard()

    await message.answer("Мы рады, что ты остался с нами!", reply_markup=build_reply_keyboard(keyboard, adjust=[2,2]))

@router.message(ProfileState.confirm_disable, F.text == "Уверен")
async def delete_form_handler(message: Message, state: FSMContext):
    await state.clear()

    await formAccessor.update_form(message.from_user.id, **{"enabled" : False})

    await message.answer("Твоя анкета теперь отключена\n<b>Возвращайся скорее!</b>", 
                         reply_markup=build_reply_keyboard([{"text": BotButtons.ENABLE_FORM.value}]), 
                         parse_mode="HTML")
    
@router.message(F.text == BotButtons.ENABLE_FORM.value)
async def delete_form_handler(message: Message):
    await formAccessor.update_form(message.from_user.id, **{"enabled" : True})
    form = await formAccessor.get_form_by_user_id(message.from_user.id)
    
    await message.answer(f"Чирик-чирик, рады снова <b>тебя</b> видеть!", 
                         parse_mode="HTML")

    await send_form_message(message, form)