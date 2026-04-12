from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.forms.models import FormImageModel, FormModel, SearchSettingsModel
from app.store.database.database import database


class FormAccessor:
    @property
    def _session(self):
        return database.get_session()
    
    async def create_form(self, user_id: int, name: str, age: int, city: int, gender: str, description: str | None, latitude: float = None, longitude: float = None) -> FormModel:        
        async with self._session as session:
            new_form = FormModel(user_id=user_id, name=name, age=age, city=city, gender=gender, description=description, latitude=latitude, longitude=longitude)
            new_settings = SearchSettingsModel(form=new_form, geo_search=True if city is not None else False)
            session.add(new_form)
            session.add(new_settings)
            await session.commit()
            await session.refresh(new_form)
            return new_form
        
    async def get_form_by_user_id(self, user_id: int) -> FormModel | None:
        async with self._session as session:
            form = await session.execute(
                select(FormModel)
                .where(FormModel.user_id == user_id)
                .options(selectinload(FormModel.images))
                .options(selectinload(FormModel.search_settings))
                )
            return form.scalar_one_or_none()
        
    async def update_form(self, user_id: int, **kwargs) -> FormModel | None:        
        async with self._session as session:
            result = await session.execute(
                select(FormModel)
                .where(FormModel.user_id == user_id)
                .options(selectinload(FormModel.images))
                .options(selectinload(FormModel.search_settings))
            )
            form = result.scalar_one_or_none()

            if not form:
                return None

            for key, value in kwargs.items():
                if hasattr(form, key):
                    setattr(form, key, value)

            if "gender_search" in kwargs or "geo_search" in kwargs:
                if not form.search_settings:
                        form.search_settings = SearchSettingsModel(form=form)

                if "gender_search" in kwargs:
                    form.search_settings.gender_search = kwargs["gender_search"]
                if "geo_search" in kwargs:
                    form.search_settings.geo_search = kwargs["geo_search"]

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
        
    async def get_search_forms(self, user_id: int, target_gender: str | None = None, lat: float = None, lon: float = None, 
                               radius_km: int = 100, exclude_ids: list[int] = None):
        async with self._session as session:
            query = select(FormModel).where(
                    FormModel.user_id != user_id, FormModel.enabled == True
                ).options(selectinload(FormModel.images))

            if target_gender is not None:
                query = query.where(FormModel.gender == target_gender)

            if exclude_ids is not None:
                query = query.where(FormModel.id.not_in(exclude_ids))

            if lat and lon:
                distance_expr = (
                    6371 * func.acos(
                        func.cos(func.radians(lat)) * 
                        func.cos(func.radians(FormModel.latitude)) * 
                        func.cos(func.radians(FormModel.longitude) - func.radians(lon)) + 
                        func.sin(func.radians(lat)) * 
                        func.sin(func.radians(FormModel.latitude))
                    )
                )
                query = query.where(distance_expr <= radius_km).order_by(distance_expr)
            else:
                query = query.order_by(func.random())

            result = await session.execute(query.limit(10))
            return result.scalars().all()
        
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

formAccessor = FormAccessor()
formImageAccessor = FormImageAccessor()