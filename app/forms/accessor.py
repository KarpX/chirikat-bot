from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.forms.models import FormImageModel, FormModel
from app.store.database.database import database


class FormAccessor:
    @property
    def _session(self):
        return database.get_session()
    
    async def create_form(self, user_id: int, name: str, age: int, city: int, gender: str, description: str | None, latitude: float = None, longitude: float = None) -> FormModel:        
        async with self._session as session:
            new_form = FormModel(user_id=user_id, name=name, age=age, city=city, gender=gender, description=description, latitude=latitude, longitude=longitude)
            session.add(new_form)
            await session.commit()
            await session.refresh(new_form)
            return new_form
        
    async def get_form_by_user_id(self, user_id: int) -> FormModel | None:
        async with self._session as session:
            form = await session.execute(
                select(FormModel)
                .where(FormModel.user_id == user_id)
                .options(selectinload(FormModel.images))
                )
            return form.scalar_one_or_none()
        
    async def update_form(self, user_id: int, **kwargs) -> FormModel | None:        
        async with self._session as session:
            result = await session.execute(
                select(FormModel)
                .where(FormModel.user_id == user_id)
                .options(selectinload(FormModel.images))
            )
            form = result.scalar_one_or_none()

            if not form:
                return None

            for key, value in kwargs.items():
                if hasattr(form, key):
                    setattr(form, key, value)

            await session.commit()
            await session.refresh(form)
            return form

    async def delete_form(self, user_id: int) -> bool:
        async with self._session as session:
            result = await session.execute(
                select(FormModel).where(FormModel.user_id == user_id)
            )
            form = result.scalar_one_or_none()
            
            if not form:
                return False

            await session.delete(form)
            await session.commit()
            return True
        
class FormImageAccessor:
    @property
    def _session(self):
        return database.get_session()
    
    async def create_form_image(self, form_id: int, file_id: str):
        async with self._session as session:
            new_image = FormImageModel(form_id=form_id, file_id=file_id)
            session.add(new_image)
            await session.commit()
            await session.refresh(new_image)
            return new_image
        
    async def get_images_by_form_id(self, form_id: int) -> list[FormImageModel]:
        async with self._session as session:
            images = await session.execute(select(FormImageModel).where(FormImageModel.form_id == form_id))
            return images.scalars().all()
        
    async def delete_images_by_form_id(self, form_id: int):
        async with self._session as session:
            await session.execute(
                delete(FormImageModel).where(FormImageModel.form_id == form_id)
            )
            await session.commit()

    async def update_form_image(self, form_id: int, file_id: str):
        await self.delete_images_by_form_id(form_id)
        return await self.create_form_image(form_id, file_id)
    
class CityAccessor:
    @property
    def _session(self):
        return database.get_session()
    
    async def get_city_by_id(self, city_id: int):
        async with self._session as session:
            city = await session.execute(select(CityModel).where(CityModel.id == city_id))
            return city.scalar_one_or_none()
        
    async def get_city_by_name(self, city_name: str):
        async with self._session as session:
            city = await session.execute(select(CityModel).where(CityModel.name == city_name))
            return city.scalar_one_or_none()


formAccessor = FormAccessor()
formImageAccessor = FormImageAccessor()
cityAccessor = CityAccessor()