from api.db import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi import HTTPException
from api.models.catalog import Building, BuildingsResult, Study, Space, GroupByResult, GroupByCount
from enacit4r_sql.utils.query import QueryBuilder


class BuildingQueryBuilder(QueryBuilder):

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
        query = query.options(selectinload(Building.certifications),
                              selectinload(Building.spaces),
                              selectinload(Building.study))
        return start, end, query

    def _apply_joins(self, query, filter):
        if "$study" in filter:
            query = query.join(Study, Study.id == Building.study_id)
        if "$space" in filter:
            query = query.join(Space, Building.id == Space.building_id)
        query = query.distinct()
        return query


class BuildingService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def count(self) -> int:
        """Count all buildings"""
        count = (await self.session.exec(text("select count(id) from building"))).scalar()
        return count

    async def get(self, building_id: int) -> Building:
        """Get a building by id"""
        res = await self.session.exec(
            select(Building).where(
                Building.id == building_id).options(selectinload(Building.certifications), selectinload(Building.spaces))
        )
        building = res.one_or_none()
        if not building:
            raise HTTPException(
                status_code=404, detail="Building not found")

        return building

    async def delete(self, building_id: int) -> Building:
        """Delete a building by id"""
        res = await self.session.exec(
            select(Building).where(Building.id == building_id)
        )
        building = res.one_or_none()
        if not building:
            raise HTTPException(
                status_code=404, detail="Building not found")
        await self.session.delete(building)
        await self.session.commit()
        return building

    async def find(self, filter: dict, sort: list, range: list) -> BuildingsResult:
        """Get all buildings matching filter and range"""
        builder = BuildingQueryBuilder(Building, filter, sort, range, {
            "$study": Study, "$space": Space})

        # Do a query to satisfy total count
        count_query = builder.build_count_query_with_joins(filter)
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query_with_joins(total_count, filter)
        if total_count == 0:
            return BuildingsResult(
                total=total_count,
                skip=start,
                limit=end - start + 1,
                data=[]
            )

        # Execute query
        results = await self.session.exec(query)
        buildings = results.all()

        return BuildingsResult(
            total=total_count,
            skip=start,
            limit=end - start + 1,
            data=buildings
        )

    async def count_group_by(self, filter: dict, group_by: str) -> dict:
        """Count all buildings matching filter"""
        builder = BuildingQueryBuilder(Building, filter, [], [], {
            "$study": Study, "$space": Space})

        # Do a query to satisfy total count
        count_query = builder.build_group_query_with_joins(
            filter, getattr(Building, group_by))
        group_by_count_res = await self.session.exec(count_query)
        group_by_counts = group_by_count_res.all()

        # Convert to dict
        return GroupByResult(
            field=group_by,
            counts=[GroupByCount(value=str(item[0]) if item[0] else None, count=item[1])
                    for item in group_by_counts])
