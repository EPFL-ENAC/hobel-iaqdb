from datetime import datetime

from api.auth import User
from api.db import AsyncSession
from api.models.catalog import Contribution, ContributionsResult, Study
from enacit4r_sql.utils.query import QueryBuilder
from fastapi import HTTPException
from sqlalchemy.sql import text
from sqlmodel import col, select


class ContributionQueryBuilder(QueryBuilder):
    pass


class ContributionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def count(self) -> int:
        """Count all contributions"""
        count = (
            await self.session.exec(text("select count(id) from contribution"))
        ).scalar()
        return count

    async def get(self, contribution_id: int) -> Contribution:
        """Get a contribution by id"""
        res = await self.session.exec(
            select(Contribution).where(Contribution.id == contribution_id)
        )
        contribution = res.one_or_none()
        if not contribution:
            raise HTTPException(status_code=404, detail="Contribution not found")
        return contribution

    async def get_by_identifier(self, study_identifier: str) -> Contribution:
        """Get a contribution by id"""
        res = await self.session.exec(
            select(Contribution).where(
                Contribution.study_identifier == study_identifier
            )
        )
        contribution = res.one_or_none()
        if not contribution:
            raise HTTPException(status_code=404, detail="Contribution not found")

        return contribution

    async def is_published(self, study_identifier: str) -> bool:
        """Whether the study is, or was, in the catalog, which shows its
        identifier: it is no longer the credential of its contributor."""
        published = select(Contribution.id).where(
            Contribution.study_identifier == study_identifier,
            col(Contribution.published_at).is_not(None),
        )
        # a study is in the catalog before its contribution is marked published
        study = select(Study.id).where(Study.identifier == study_identifier)
        for statement in (published, study):
            if (await self.session.exec(statement)).first() is not None:
                return True
        return False

    async def delete(self, contribution_id: int) -> Contribution:
        """Delete a contribution by id"""
        res = await self.session.exec(
            select(Contribution).where(Contribution.id == contribution_id)
        )
        contribution = res.one_or_none()
        if not contribution:
            raise HTTPException(status_code=404, detail="Contribution not found")
        await self.session.delete(contribution)
        await self.session.commit()
        return contribution

    async def delete_by_identifier(self, study_identifier: str) -> Contribution:
        """Delete a contribution by study identifier"""
        res = await self.session.exec(
            select(Contribution).where(
                Contribution.study_identifier == study_identifier
            )
        )
        contribution = res.one_or_none()
        if not contribution:
            raise HTTPException(status_code=404, detail="Contribution not found")
        await self.session.delete(contribution)
        await self.session.commit()
        return contribution

    async def find(self, filter: dict, sort: list, range: list) -> ContributionsResult:
        """Get all contributions matching filter and range"""
        builder = ContributionQueryBuilder(Contribution, filter, sort, range)

        # Do a query to satisfy total count
        count_query = builder.build_count_query()
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query(total_count)
        if total_count == 0:
            return ContributionsResult(
                total=total_count, skip=start, limit=end - start + 1, data=[]
            )

        # Execute query
        results = await self.session.exec(query)
        contributions = results.all()

        return ContributionsResult(
            total=total_count, skip=start, limit=end - start + 1, data=contributions
        )

    async def create(self, payload: Contribution, user: User = None) -> Contribution:
        """Create a new contribution"""
        contribution = Contribution(**payload.model_dump())
        contribution.created_at = datetime.now()
        contribution.updated_at = datetime.now()
        contribution.created_by = user.username if user else None
        contribution.updated_by = user.username if user else None
        self.session.add(contribution)
        await self.session.commit()
        return contribution

    async def update(
        self, study_identifier: str, payload: Contribution, user: User = None
    ) -> Contribution:
        """Update a contribution by study identifier"""
        res = await self.session.exec(
            select(Contribution).where(
                Contribution.study_identifier == study_identifier
            )
        )
        contribution = res.one_or_none()
        if not contribution:
            raise HTTPException(status_code=404, detail="Contribution not found")
        for key, value in payload.model_dump().items():
            if key not in [
                "id",
                "study_identifier",
                "created_at",
                "updated_at",
                "created_by",
                "updated_by",
                "published_at",
                "published_by",
            ]:
                setattr(contribution, key, value)
        contribution.updated_at = datetime.now()
        contribution.updated_by = user.username if user else None
        await self.session.commit()
        return contribution

    async def touch_by_identifier(
        self, study_identifier: str, user: User = None
    ) -> Contribution:
        """Touch a contribution by study identifier"""
        res = await self.session.exec(
            select(Contribution).where(
                Contribution.study_identifier == study_identifier
            )
        )
        contribution = res.one_or_none()
        if not contribution:
            contribution = await self.create(
                Contribution(study_identifier=study_identifier), user
            )
        else:
            contribution.updated_at = datetime.now()
            contribution.updated_by = user.username if user else None
            await self.session.commit()
        return contribution

    async def publish_by_identifier(
        self, study_identifier: str, user: User = None
    ) -> Contribution:
        """Publish a contribution by study identifier"""
        res = await self.session.exec(
            select(Contribution).where(
                Contribution.study_identifier == study_identifier
            )
        )
        contribution = res.one_or_none()
        if not contribution:
            contribution = await self.create(
                Contribution(study_identifier=study_identifier), user
            )
        contribution.published_at = datetime.now()
        contribution.published_by = user.username if user else None
        await self.session.commit()
        return contribution
