from api.db import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy import func
from sqlmodel import select
from fastapi import HTTPException
from api.models.catalog import Building, Study, Space, SpacesResult, GroupByResult, GroupByCount
from enacit4r_sql.utils.query import QueryBuilder


class SpaceQueryBuilder(QueryBuilder):

    def build_count_query_with_joins(self, filter):
        query = self.build_count_query()
        query = self._apply_joins(query, filter)
        return query

    def build_group_query_with_joins(self, filter, group_by_column):
        query = self._apply_filter(
            select(group_by_column, func.count(func.distinct(self.model.id))))
        query = self._apply_joins(query, filter)
        return query.group_by(group_by_column)

    def build_query_with_joins(self, total_count, filter):
        start, end, query = self.build_query(total_count)
        query = self._apply_joins(query, filter)
        # query = query.options(selectinload(Space.building))
        return start, end, query

    def _apply_joins(self, query, filter):
        if "$study" in filter:
            query = query.join(Study, Study.id == Space.study_id)
        if "$building" in filter:
            query = query.join(Space, Building.id == Space.building_id)
        query = query.distinct()
        return query


class SpaceService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def count(self) -> int:
        """Count all spaces"""
        count = (await self.session.exec(text("select count(id) from space"))).scalar()
        return count

    async def get(self, space_id: int) -> Space:
        """Get a space by id"""
        res = await self.session.exec(
            select(Space).where(
                Space.id == space_id)
        )
        space = res.one_or_none()
        if not space:
            raise HTTPException(
                status_code=404, detail="Space not found")

        return space

    async def delete(self, space_id: int) -> Study:
        """Delete a space by id"""
        res = await self.session.exec(
            select(Space).where(Space.id == space_id)
        )
        space = res.one_or_none()
        if not space:
            raise HTTPException(
                status_code=404, detail="Space not found")
        await self.session.delete(space)
        await self.session.commit()
        return space

    async def find(self, filter: dict, sort: list, range: list) -> SpacesResult:
        """Get all spaces matching filter and range"""
        builder = SpaceQueryBuilder(Space, filter, sort, range, {
            "$study": Study, "$building": Building})

        # Do a query to satisfy total count
        count_query = builder.build_count_query_with_joins(filter)
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query_with_joins(total_count, filter)

        # Execute query
        results = await self.session.exec(query)
        spaces = results.all()

        return SpacesResult(
            total=total_count,
            skip=start,
            limit=end - start + 1,
            data=spaces
        )

    async def count_group_by(self, filter: dict, group_by: str) -> dict:
        """Count all spaces matching filter"""
        builder = SpaceQueryBuilder(Space, filter, [], [], {
            "$study": Study, "$building": Building})

        # Do a query to satisfy total count
        count_query = builder.build_group_query_with_joins(
            filter, getattr(Space, group_by))
        group_by_count_res = await self.session.exec(count_query)
        group_by_counts = group_by_count_res.all()

        # Convert to dict
        return GroupByResult(
            field=group_by,
            counts=[GroupByCount(value=str(item[0]) if item[0] else None, count=item[1])
                    for item in group_by_counts])
