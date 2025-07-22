from api.db import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi import HTTPException
from api.models.catalog import Study, Instrument, InstrumentsResult, InstrumentParameter
from enacit4r_sql.utils.query import QueryBuilder


class InstrumentQueryBuilder(QueryBuilder):

    def build_count_query_with_joins(self, filter):
        query = self.build_count_query()
        query = self._apply_joins(query, filter)
        return query

    def build_query_with_joins(self, total_count, filter):
        start, end, query = self.build_query(total_count)
        query = self._apply_joins(query, filter)
        query = query.options(selectinload(Instrument.parameters))
        return start, end, query

    def _apply_joins(self, query, filter):
        if "$study" in filter:
            query = query.join(Study, Study.id == Instrument.study_id)
        if "$instrumentparameter" in filter:
            query = query.join(InstrumentParameter, Instrument.id ==
                               InstrumentParameter.instrument_id)
        query = query.distinct()
        return query


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
                Instrument.id == instrument_id).options(selectinload(Instrument.parameters))
        )
        instrument = res.one_or_none()
        if not instrument:
            raise HTTPException(
                status_code=404, detail="Instrument not found")

        return instrument

    async def delete(self, instrument_id: int) -> Instrument:
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
        builder = InstrumentQueryBuilder(Instrument, filter, sort,
                                         range, {"$study": Study, "$instrumentparameter": InstrumentParameter})

        # Do a query to satisfy total count
        count_query = builder.build_count_query_with_joins(filter)
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query_with_joins(total_count, filter)
        if total_count == 0:
            return InstrumentsResult(
                total=total_count,
                skip=start,
                limit=end - start + 1,
                data=[]
            )

        # Execute query
        results = await self.session.exec(query)
        instruments = results.all()

        return InstrumentsResult(
            total=total_count,
            skip=start,
            limit=end - start + 1,
            data=instruments
        )
