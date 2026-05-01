from http.client import HTTPException

from sqlalchemy import delete, func, literal, not_, select
from sqlalchemy.orm import selectinload

from app.forms.models import FormImageModel, FormLikeModel, FormModel, MatchModel, SearchSettingsModel
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
            my_form = await self.get_form_by_user_id(user_id)

            liked_ids_query = await session.execute(
                select(FormLikeModel.liked_form_id)
                .where(FormLikeModel.like_from == my_form.id)
            )
            liked_ids = liked_ids_query.scalars().all()

            all_exclude = list(exclude_ids or []) + liked_ids

            filters = [FormModel.user_id != user_id, FormModel.enabled == True]
            if target_gender:
                filters.append(FormModel.gender == target_gender)
            if all_exclude:
                filters.append(not_(FormModel.id.in_(all_exclude)))

            distance_expr = None
            if lat is not None and lon is not None:
                distance_expr = (
                    6371 * func.acos(
                        func.cos(func.radians(lat)) * 
                        func.cos(func.radians(FormModel.latitude)) * 
                        func.cos(func.radians(FormModel.longitude) - func.radians(lon)) + 
                        func.sin(func.radians(lat)) * 
                        func.sin(func.radians(FormModel.latitude))
                    )
                )
                query = select(FormModel, distance_expr.label("dist")).where(*filters, distance_expr <= radius_km).order_by(distance_expr)
            else:
                query = select(FormModel, literal(None).label("dist")).where(*filters).order_by(func.random())

            result = await session.execute(query.limit(10))
            
            forms_with_dist = []
            for row in result.all():
                form = row[0]
                dist = row[1]
                form.distance_km = round(float(dist), 1) if dist is not None else None
                forms_with_dist.append(form)
                
            return forms_with_dist
        
    async def add_like(self, from_user_id: int, to_form_id: int):
        async with self._session as session:
            from_form = await self.get_form_by_user_id(from_user_id)

            existing = await session.execute(
                select(FormLikeModel).where(
                    FormLikeModel.liked_form_id == to_form_id,
                    FormLikeModel.like_from == from_form.id
                )
            )
            if existing.scalar_one_or_none():
                return False, None
            
            new_like = FormLikeModel(like_from=from_form.id, liked_form_id=to_form_id)
            session.add(new_like)

            match_check = await session.execute(
                select(FormLikeModel).where(
                    FormLikeModel.like_from == to_form_id,
                    FormLikeModel.liked_form_id == from_form.id
                )
            )
            is_match = match_check.scalar_one_or_none() is not None

            if is_match:
                match = MatchModel(form1_id=from_form.id, form2_id=to_form_id)
                session.add(match)
            
            await session.commit()
            return True, is_match
        
    async def get_sympathy_forms(self, user_id: int):
        async with self._session as session:
            my_form = await self.get_form_by_user_id(user_id)
            if not my_form:
                return []

            liked_by_query = select(FormLikeModel.like_from).where(
                FormLikeModel.liked_form_id == my_form.id
            )
            
            query = select(FormModel).where(
                FormModel.id.in_(liked_by_query),
                FormModel.enabled == True
            ).options(selectinload(FormModel.images))
            
            result = await session.execute(query)
            return result.scalars().all()
        
    async def delete_like(self, from_form_id: int, to_form_id: int):
        async with self._session as session:
            result = await session.execute(
                select(FormLikeModel)
                .where(
                    FormLikeModel.like_from == from_form_id,
                    FormLikeModel.liked_form_id == to_form_id
                )
            )
            like = result.scalar_one_or_none()

            if not like:
                return False
            
            await session.delete(like)
            await session.commit()
            return True
    
    async def get_matches(self, user_id: int):
        async with self._session as session:
            my_form = await self.get_form_by_user_id(user_id)
            if not my_form:
                return []

            matches_query = select(MatchModel).where(
                (MatchModel.form1_id == my_form.id) | (MatchModel.form2_id == my_form.id)
            )

            result = await session.execute(matches_query)
            matches = result.scalars().all()

            matched_forms = []
            for match in matches:
                other_form_id = match.form2_id if match.form1_id == my_form.id else match.form1_id
                other_form_query = select(FormModel).where(FormModel.id == other_form_id).options(selectinload(FormModel.images))
                other_result = await session.execute(other_form_query)
                other_form = other_result.scalar_one_or_none()
                if other_form and other_form.enabled:
                    matched_forms.append(other_form)

            return matched_forms
        

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