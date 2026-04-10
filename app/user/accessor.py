from sqlalchemy import select

from app.store.database.database import database
from app.user.models import UserModel


class UserAccessor:    
    @property
    def _session(self):
        return database.get_session()
    
    async def get_user(self, user_id: int):
        async with self._session as session:
            user = await session.execute(select(UserModel).where(UserModel.id == user_id))
            return user.scalar_one_or_none()

    async def create_or_get_user(self, user_id: int, username: str | None = None):
        async with self._session as session:
            user = await session.execute(select(UserModel).where(UserModel.id == user_id))
            user = user.scalar_one_or_none()

            if user:
                if username and user.username != username:
                    user = await self.update_user(user_id, username)
                return user

            new_user = UserModel(id=user_id, username=username)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user
        
    async def update_user(self, user_id: int, username: str):
        async with self._session as session:
            user = await session.execute(select(UserModel).where(UserModel.id == user_id))
            user = user.scalar_one_or_none()

            if not user:
                return None

            user.username = username
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        
    async def delete_user(self, user_id: int) -> bool:
        async with self._session as session:
            user = await session.execute(select(UserModel).where(UserModel.id == user_id))
            user = user.scalar_one_or_none()
            
            if not user:
                return False

            await session.delete(user)
            await session.commit()
            return True

userAccessor = UserAccessor()