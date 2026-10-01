import sys

from api.config import config
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

# Don't load engine if pytest is running
if "pytest" not in sys.modules:
    # The Explore page fires its charts in parallel: the pool must cover them
    engine = create_async_engine(
        config.DB_URL, echo=False, future=True, pool_size=20, max_overflow=10
    )


async def get_session() -> AsyncSession:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


def get_engine() -> AsyncEngine:
    """The engine, for work that outlives the request session (background
    loads, continuous aggregate refreshes)."""
    return engine
