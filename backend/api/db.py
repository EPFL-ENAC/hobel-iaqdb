import sys

from api.config import config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

# Don't load engine if pytest is running
if "pytest" not in sys.modules:
    engine = create_async_engine(config.DB_URL, echo=True, future=True)


async def get_session() -> AsyncSession:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
