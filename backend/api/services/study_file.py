from typing import Iterable, Literal

from api.db import AsyncSession
from api.models.catalog import StudyFile
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col, delete, select

Area = Literal["draft", "pub"]


class StudyFileService:
    """The S3 files index of the studies. Callers commit."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def keys(self, identifier: str, area: Area) -> list[str]:
        res = await self.session.exec(
            select(StudyFile.key)
            .where(StudyFile.study_identifier == identifier, StudyFile.area == area)
            .order_by(StudyFile.key)
        )
        return list(res.all())

    async def add(self, identifier: str, area: Area, keys: Iterable[str]) -> None:
        rows = [
            {"key": key, "study_identifier": identifier, "area": area} for key in keys
        ]
        if rows:
            await self.session.exec(
                insert(StudyFile).values(rows).on_conflict_do_nothing()
            )

    async def remove(
        self, identifier: str, area: Area, keys: Iterable[str] | None = None
    ) -> list[str]:
        """Remove the given keys, all of the area when None, from the index.
        Returns the removed keys, for the caller to delete from S3 once
        committed: a failed S3 delete leaves an orphan, never a dangling key."""
        statement = delete(StudyFile).where(
            StudyFile.study_identifier == identifier, StudyFile.area == area
        )
        if keys is not None:
            statement = statement.where(col(StudyFile.key).in_(list(keys)))
        res = await self.session.exec(statement.returning(StudyFile.key))
        return list(res.scalars().all())
