from sqlalchemy import select

from app.store.database.database import database
from app.user.models import UserModel


class UserAccessor:    
    @property
    def _session(self):
        return database.get_session()
    
    # async def get_user(self, user_id: int):
    #     return await self.session.query(UserModel).filter_by(user_id=user_id).first()

    async def create_or_get_user(self, user_id: int, username: str | None = None):
        async with self._session as session:
            user = await session.execute(select(UserModel).where(UserModel.id == user_id))
            user = user.scalar_one_or_none()
            if user:
                return user

            new_user = UserModel(id=user_id, username=username)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user

userAccessor = UserAccessor()