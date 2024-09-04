from api.db import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi import HTTPException
from api.models.catalog import Study, Instrument, InstrumentsResult
from api.utils.query import QueryBuilder


class InstrumentService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def count(self) -> int:
        """Count all instruments"""
        count = (await self.session.exec(text("select count(id) from instrument"))).scalar()
        return count

    async def get(self, instrument_id: int) -> Instrument:
        """Get a instrument by id"""
        res = await self.session.exec(
            select(Instrument).where(
                Instrument.id == instrument_id)
        )
        instrument = res.one_or_none()
        if not instrument:
            raise HTTPException(
                status_code=404, detail="Instrument not found")

        return instrument

    async def delete(self, instrument_id: int) -> Study:
        """Delete a instrument by id"""
        res = await self.session.exec(
            select(Instrument).where(Instrument.id == instrument_id)
        )
        instrument = res.one_or_none()
        if not instrument:
            raise HTTPException(
                status_code=404, detail="Instrument not found")
        await self.session.delete(instrument)
        await self.session.commit()
        return instrument

    async def find(self, filter: dict, sort: list, range: list) -> InstrumentsResult:
        """Get all instruments matching filter and range"""
        builder = QueryBuilder(Instrument, filter, sort,
                               range, {"$study": Study})

        # Do a query to satisfy total count
        count_query = self.apply_joins(builder.build_count_query(), filter)
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query(total_count)
        query = self.apply_joins(query, filter)

        # Execute query
        results = await self.session.exec(query)
        instruments = results.all()

        return InstrumentsResult(
            total=total_count,
            skip=start,
            limit=end - start + 1,
            data=instruments
        )

    def apply_joins(self, query, filter):
        if "$study" in filter:
            query = query.join(Study, Study.id == Instrument.study_id)
        query = query.distinct()
        return query
