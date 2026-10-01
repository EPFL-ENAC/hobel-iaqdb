"""One integer that changes whenever published data changes. Every cache key
of the explore routes carries it, so no result outlives its data."""

from api.db import AsyncSession
from api.models.measurement import CatalogVersion
from sqlalchemy import update
from sqlmodel import select

CATALOG_VERSION_ID = 1


class CatalogVersionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self) -> int:
        result = await self.session.exec(
            select(CatalogVersion.version).where(
                CatalogVersion.id == CATALOG_VERSION_ID
            )
        )
        version = result.one_or_none()
        if version is None:
            raise RuntimeError("catalog_version row is missing: run the migrations")
        return version

    async def bump(self) -> int:
        """Increment the version; the caller commits (route transaction)."""
        result = await self.session.exec(
            update(CatalogVersion)
            .where(CatalogVersion.id == CATALOG_VERSION_ID)
            .values(version=CatalogVersion.version + 1)
            .returning(CatalogVersion.version)
        )
        version = result.scalar_one_or_none()
        if version is None:
            raise RuntimeError("catalog_version row is missing: run the migrations")
        return version
