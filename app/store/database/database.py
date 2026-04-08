from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

class Database:
    def __init__(self):
        self.session_maker = None
        self.engine = None

    async def connect(self):
        DATABASE_URL = "postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
        self.engine = create_async_engine(DATABASE_URL, echo=True)
        self.session_maker = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def get_session(self) -> AsyncSession:
        if self.session_maker is None:
            raise Exception("Database not connected. Call connect() first.")
        return self.session_maker()
    
    async def disconnect(self):
        if self.engine is not None:
            await self.engine.dispose()