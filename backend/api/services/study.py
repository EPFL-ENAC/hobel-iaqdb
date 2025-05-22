from api.db import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi import HTTPException
from api.models.catalog import Study, StudiesResult, Building, Space
from enacit4r_sql.utils.query import QueryBuilder


class StudyQueryBuilder(QueryBuilder):

    def build_count_query_with_joins(self, filter):
        query = self.build_count_query()
        query = self._apply_joins(query, filter)
        return query

    def build_query_with_joins(self, total_count, filter):
        start, end, query = self.build_query(total_count)
        query = self._apply_joins(query, filter)
        query = query.options(selectinload(Study.contributors),
                              selectinload(Study.buildings),
                              selectinload(Study.instruments))
        return start, end, query

    def _apply_joins(self, query, filter):
        if "$building" in filter:
            query = query.join(Building, Study.id == Building.study_id)
        if "$space" in filter:
            query = query.join(Space, Study.id == Space.study_id)
        query = query.distinct()
        return query


class StudyService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def count(self) -> int:
        """Count all studies"""
        count = (await self.session.exec(text("select count(id) from study"))).scalar()
        return count

    async def get(self, study_id: int) -> Study:
        """Get a study by id"""
        res = await self.session.exec(
            select(Study).where(
                Study.id == study_id).options(selectinload(Study.contributors), selectinload(Study.buildings), selectinload(Study.instruments))
        )
        study = res.one_or_none()
        if not study:
            raise HTTPException(
                status_code=404, detail="Study not found")

        return study

    async def delete(self, study_id: int) -> Study:
        """Delete a study by id"""
        res = await self.session.exec(
            select(Study).where(Study.id == study_id)
        )
        study = res.one_or_none()
        if not study:
            raise HTTPException(
                status_code=404, detail="Study not found")
        await self.session.delete(study)
        await self.session.commit()
        return study

    async def find(self, filter: dict, sort: list, range: list) -> StudiesResult:
        """Get all studies matching filter and range"""
        builder = StudyQueryBuilder(Study, filter, sort, range, {
            "$building": Building, "$space": Space})

        # Do a query to satisfy total count
        count_query = builder.build_count_query_with_joins(filter)
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query_with_joins(total_count, filter)
        if total_count == 0:
            return StudiesResult(
                total=total_count,
                skip=start,
                limit=end - start + 1,
                data=[]
            )

        # Execute query
        results = await self.session.exec(query)
        studies = results.all()

        return StudiesResult(
            total=total_count,
            skip=start,
            limit=end - start + 1,
            data=studies
        )
