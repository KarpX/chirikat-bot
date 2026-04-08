from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import os

from app.store.database.sql_alchemy_base import BaseModel

class Database:
    def __init__(self):
        self.engine = None
        self.sessionmaker: async_sessionmaker | None = None
        self.database = BaseModel

    async def connect(self, *args, **kwargs):
        DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT_EXTERNAL')}/{os.getenv('DB_NAME')}"
        self.engine = create_async_engine(DATABASE_URL, echo=True)
        self.sessionmaker = async_sessionmaker(self.engine, expire_on_commit=False)

    def get_session(self) -> AsyncSession:
        if self.sessionmaker is None:
            raise Exception("Database not connected. Call connect() first.")
        return self.sessionmaker()
    
    async def disconnect(self, *args, **kwargs):
        if self.engine is not None:
            await self.engine.dispose()

database = Database()