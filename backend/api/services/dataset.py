from api.db import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi import HTTPException
from api.models.catalog import Dataset, DatasetsResult, Study, Variable
from api.utils.query import QueryBuilder


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

    async def delete(self, dataset_id: int) -> Study:
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
        builder = QueryBuilder(Dataset, filter, sort, range, {
                               "$study": Study, "$variable": Variable})

        # Do a query to satisfy total count
        count_query = self.apply_joins(builder.build_count_query(), filter)
        total_count_query = await self.session.exec(count_query)
        total_count = total_count_query.one()

        # Main query
        start, end, query = builder.build_query(total_count)
        query = self.apply_joins(query, filter)
        query = query.options(selectinload(
            Dataset.variables), selectinload(Dataset.study))

        # Execute query
        results = await self.session.exec(query)
        datasets = results.all()

        return DatasetsResult(
            total=total_count,
            skip=start,
            limit=end - start + 1,
            data=datasets
        )

    def apply_joins(self, query, filter):
        if "$study" in filter:
            query = query.join(Study, Study.id == Dataset.study_id)
        if "$variable" in filter:
            query = query.join(Variable, Dataset.id == Variable.dataset_id)
        query = query.distinct()
        return query
