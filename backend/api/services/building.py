from api.db import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi import HTTPException
from api.models.catalog import Building, BuildingsResult
from api.utils.query import QueryBuilder


class BuildingService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def count(self) -> int:
        """Count all buildings"""
        count = (await self.session.exec(text("select count(id) from building"))).scalar()
        return count

    async def get(self, building_id: int) -> Building:
        """Get a numerical model by id"""
        res = await self.session.exec(
            select(Building).where(
                Building.id == building_id).options(selectinload(Building.certifications), selectinload(Building.spaces))
        )
        building = res.one_or_none()
        if not building:
            raise HTTPException(
                status_code=404, detail="Building not found")

        return building

    async def find(self, filter: dict, sort: list, range: list) -> BuildingsResult:
        """Get all studies matching filter and range"""
        builder = QueryBuilder(Building, filter, sort, range)

        # Do a query to satisfy total count
        count_query = builder.build_count_query()
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query(total_count)
        query = query.options(selectinload(
            Building.certifications), selectinload(Building.spaces))

        # Execute query
        results = await self.session.exec(query)
        buildings = results.all()

        return BuildingsResult(
            total=total_count,
            skip=start,
            limit=end - start + 1,
            data=buildings
        )
