import json

from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType

from app.user.models import FSMStorageModel

class SQLAlchemyStorage(BaseStorage):
    def __init__(self, db):
        self.db = db

    async def set_state(self, key: StorageKey, state: StateType = None):
        async with self.db.get_session() as session:
            s_key = f"{key.bot_id}:{key.chat_id}:{key.user_id}"
            state_str = state.state if hasattr(state, 'state') else state
            
            exists = await session.get(FSMStorageModel, s_key)
            if exists:
                exists.state = state_str
            else:
                session.add(FSMStorageModel(key=s_key, state=state_str))
            await session.commit()

    async def get_state(self, key: StorageKey) -> str | None:
        async with self.db.get_session() as session:
            s_key = f"{key.bot_id}:{key.chat_id}:{key.user_id}"
            res = await session.get(FSMStorageModel, s_key)
            return res.state if res else None

    async def set_data(self, key: StorageKey, data: dict):
        async with self.db.get_session() as session:
            s_key = f"{key.bot_id}:{key.chat_id}:{key.user_id}"
            data_str = json.dumps(data)
            
            exists = await session.get(FSMStorageModel, s_key)
            if exists:
                exists.data = data_str
            else:
                session.add(FSMStorageModel(key=s_key, data=data_str))
            await session.commit()

    async def get_data(self, key: StorageKey) -> dict:
        async with self.db.get_session() as session:
            s_key = f"{key.bot_id}:{key.chat_id}:{key.user_id}"
            res = await session.get(FSMStorageModel, s_key)
            return json.loads(res.data) if res and res.data else {}
        
    async def close(self) -> None:
        pass