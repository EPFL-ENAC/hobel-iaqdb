from api.db import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi import HTTPException
from api.models.catalog import Dataset, DatasetsResult, Study, Variable
from enacit4r_sql.utils.query import QueryBuilder


class DatasetQueryBuilder(QueryBuilder):

    def build_count_query_with_joins(self, filter):
        query = self.build_count_query()
        query = self._apply_joins(query, filter)
        return query

    def build_query_with_joins(self, total_count, filter):
        start, end, query = self.build_query(total_count)
        query = self._apply_joins(query, filter)
        query = query.options(selectinload(Dataset.variables),
                              selectinload(Dataset.study))
        return start, end, query

    def _apply_joins(self, query, filter):
        if "$study" in filter:
            query = query.join(Study, Study.id == Dataset.study_id)
        if "$variable" in filter:
            query = query.join(Variable, Dataset.id == Variable.dataset_id)
        query = query.distinct()
        return query


class DatasetService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def count(self) -> int:
        """Count all datasets"""
        count = (await self.session.exec(text("select count(id) from dataset"))).scalar()
        return count

    async def get(self, dataset_id: int) -> Dataset:
        """Get a dataset by id"""
        res = await self.session.exec(
            select(Dataset).where(
                Dataset.id == dataset_id).options(selectinload(Dataset.variables))
        )
        dataset = res.one_or_none()
        if not dataset:
            raise HTTPException(
                status_code=404, detail="Dataset not found")

        return dataset

    async def delete(self, dataset_id: int) -> Dataset:
        """Delete a dataset by id"""
        res = await self.session.exec(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        dataset = res.one_or_none()
        if not dataset:
            raise HTTPException(
                status_code=404, detail="Dataset not found")
        await self.session.delete(dataset)
        await self.session.commit()
        return dataset

    async def find(self, filter: dict, sort: list, range: list) -> DatasetsResult:
        """Get all datasets matching filter and range"""
        builder = DatasetQueryBuilder(Dataset, filter, sort, range, {
            "$study": Study, "$variable": Variable})

        # Do a query to satisfy total count
        count_query = builder.build_count_query_with_joins(filter)
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query_with_joins(total_count, filter)
        if total_count == 0:
            return DatasetsResult(
                total=total_count,
                skip=start,
                limit=end - start + 1,
                data=[]
            )

        # Execute query
        results = await self.session.exec(query)
        datasets = results.all()

        return DatasetsResult(
            total=total_count,
            skip=start,
            limit=end - start + 1,
            data=datasets
        )
