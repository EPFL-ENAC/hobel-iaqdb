"""`GET /stats/measurements`: group-by over `measurement_day`,
`measurement_hour` or the raw hypertable."""

from api.models.catalog import Building, Dataset, Space, Study
from api.models.explore import (
    Bucket,
    Coverage,
    Exceedance,
    ExploreQuery,
    ExploreResult,
    Meta,
    Stats,
)
from api.models.measurement import DatasetParameter
from api.services.explore.dimensions import DimensionSpec, Frame, resolve
from api.services.explore.envelope import (
    check_parameters,
    common_unit,
    finish,
    key_text,
    number,
)
from api.services.explore.facts import Fact, check_raw_cap
from api.services.explore.filters import apply_joined_filter, parse_filter
from fastapi import HTTPException
from sqlalchemy import func, literal_column
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

AGGS = ("coverage", "count", "stats", "exceedance")
PERCENTILES = literal_column("ARRAY[0.05, 0.25, 0.5, 0.75, 0.95]")


class MeasurementQueryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def query(self, query: ExploreQuery, version: int) -> ExploreResult:
        agg = query.agg or "count"
        if agg not in AGGS:
            raise HTTPException(status_code=422, detail=f"agg must be one of {AGGS}")
        grain = query.grain or "day"
        filter = parse_filter(query.filter)
        parameters = await check_parameters(self.session, query.parameters)
        specs = resolve(query.by, grain)
        if agg == "coverage":
            buckets = await self._coverage(query, filter, specs)
        else:
            if grain == "raw":
                await check_raw_cap(self.session, filter, query.parameters)
            buckets = await self._aggregate(agg, grain, query, filter, specs)
        meta = Meta(
            source="measurements",
            agg=agg,
            grain=grain,
            dimensions=[s.key for s in specs],
            parameters=query.parameters,
            unit=common_unit(parameters),
            **{"from": query.from_},
            to=query.to,
            n=0,
            version=version,
        )
        return await finish(self.session, query, filter, meta, buckets, specs)

    async def _aggregate(self, agg, grain, query, filter, specs) -> list[Bucket]:
        fact = Fact(grain)
        frame = fact.frame()
        keys = [spec.column(frame) for spec in specs]
        measures = self._measures(agg, fact, query)
        statement = select(*keys, func.count(), fact.records(), *measures)
        statement = fact.where(statement, query, filter, query.parameters)
        statement = statement.select_from(frame.select_from).group_by(*keys)
        rows = (await self.session.exec(statement)).all()
        # without keys an empty scan still yields one row of count 0
        return [
            self._bucket(agg, query, len(keys), row) for row in rows if row[len(keys)]
        ]

    def _measures(self, agg: str, fact: Fact, query: ExploreQuery) -> list:
        value = fact.value
        if agg == "count":
            return []
        if agg == "exceedance":
            if query.threshold is None:
                raise HTTPException(
                    status_code=422, detail="exceedance needs threshold"
                )
            return [func.count().filter(value > query.threshold)]
        # stats: at day/hour these are statistics of bucket means, weighted
        # mean excepted; at raw, of the readings themselves
        mean = (
            func.sum(value * fact.n) / func.sum(fact.n)
            if fact.n is not None
            else func.avg(value)
        )
        return [
            mean,
            func.stddev_samp(value),
            func.min(value),
            func.max(value),
            func.percentile_cont(PERCENTILES).within_group(value),
        ]

    def _bucket(self, agg: str, query: ExploreQuery, width: int, row) -> Bucket:
        key = [key_text(v) for v in row[:width]]
        n, n_records = int(row[width]), int(row[width + 1])
        bucket = Bucket(key=key, n=n, n_records=n_records)
        if agg == "exceedance":
            n_above = int(row[width + 2])
            bucket.exceedance = Exceedance(
                threshold=query.threshold, n_above=n_above, share=n_above / n
            )
        if agg == "stats":
            mean, sd, lo, hi, percentiles = row[width + 2 : width + 7]
            bucket.stats = Stats(
                mean=number(mean),
                sd=number(sd),
                min=number(lo),
                p05=number(percentiles[0]),
                p25=number(percentiles[1]),
                p50=number(percentiles[2]),
                p75=number(percentiles[3]),
                p95=number(percentiles[4]),
                max=number(hi),
            )
        return bucket

    async def _coverage(
        self, query, filter, specs: list[DimensionSpec]
    ) -> list[Bucket]:
        """From `dataset_parameter` only, no fact scan. Datasets are
        deduplicated per key before summing, since a study's buildings and
        spaces fan out the join."""
        frame = coverage_frame()
        keys = [spec.column(frame).label(f"k{i}") for i, spec in enumerate(specs)]
        dp = DatasetParameter
        inner = select(
            *keys,
            col(dp.dataset_id).label("dataset_id"),
            col(dp.parameter).label("parameter"),
            col(dp.n_records).label("n_records"),
            col(dp.n_missing).label("n_missing"),
            col(dp.first_at).label("first_at"),
            col(dp.last_at).label("last_at"),
        ).distinct()
        inner = apply_joined_filter(frame, inner, filter)
        if query.parameters:
            inner = inner.where(col(dp.parameter).in_(query.parameters))
        if query.from_:
            inner = inner.where(col(dp.last_at) >= query.from_)
        if query.to:
            inner = inner.where(col(dp.first_at) < query.to)
        sub = inner.select_from(frame.select_from).subquery()
        group = [sub.c[f"k{i}"] for i in range(len(keys))]
        statement = (
            select(
                *group,
                func.count(),
                func.sum(sub.c.n_records),
                func.count(func.distinct(sub.c.dataset_id)),
                func.sum(sub.c.n_missing),
                func.min(sub.c.first_at),
                func.max(sub.c.last_at),
            )
            .select_from(sub)
            .group_by(*group)
        )
        rows = (await self.session.exec(statement)).all()
        width = len(keys)
        return [
            Bucket(
                key=[key_text(v) for v in row[:width]],
                n=int(row[width]),
                n_records=int(row[width + 1]),
                coverage=Coverage(
                    n_datasets=int(row[width + 2]),
                    n_missing=int(row[width + 3]),
                    first_at=row[width + 4],
                    last_at=row[width + 5],
                ),
            )
            for row in rows
            if row[width]
        ]


def coverage_frame() -> Frame:
    dp = DatasetParameter
    available = {
        "dataset": (Dataset, col(Dataset.id) == col(dp.dataset_id), ()),
        "study": (Study, col(Study.id) == col(Dataset.study_id), ("dataset",)),
        "building": (
            Building,
            col(Building.study_id) == col(Dataset.study_id),
            ("dataset",),
        ),
        "space": (Space, col(Space.study_id) == col(Dataset.study_id), ("dataset",)),
    }
    return Frame("parameter", dp, available, time=None, parameter=col(dp.parameter))
