from api.db import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi import HTTPException
from api.models.catalog import Building, BuildingsResult, Study, Space
from api.utils.query import QueryBuilder


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

    async def delete(self, building_id: int) -> Study:
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
        builder = QueryBuilder(Building, filter, sort, range, {
                               "$study": Study, "$space": Space})

        # Do a query to satisfy total count
        count_query = self.apply_joins(builder.build_count_query(), filter)
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query(total_count)
        query = self.apply_joins(query, filter)
        query = query.options(selectinload(
            Building.certifications), selectinload(Building.spaces), selectinload(Building.study))

        # Execute query
        results = await self.session.exec(query)
        buildings = results.all()

        return BuildingsResult(
            total=total_count,
            skip=start,
            limit=end - start + 1,
            data=buildings
        )

    def apply_joins(self, query, filter):
        if "$study" in filter:
            query = query.join(Study, Study.id == Building.study_id)
        if "$space" in filter:
            query = query.join(Space, Building.id == Space.building_id)
        query = query.distinct()
        return query
