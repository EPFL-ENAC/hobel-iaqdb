"""`GET /stats/relationships`: pairwise queries over co-located, co-timed
measurements (same dataset, space and time bucket)."""

import math

from api.models.catalog import Building, Space
from api.models.explore import Bucket, ExploreQuery, ExploreResult, Fit, Meta
from api.services.explore.dimensions import resolve
from api.services.explore.envelope import (
    check_parameters,
    common_unit,
    finish,
    key_text,
    number,
)
from api.services.explore.facts import Fact, check_raw_cap
from api.services.explore.filters import parse_filter
from api.services.explore.schema import METRICS
from fastapi import HTTPException
from sqlalchemy import and_, case, func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

AGGS = ("pairs", "matrix")
# points a pairs chart gets at most; the fit is always over every row
SAMPLE = 2000
METRIC_MODELS = {"space": Space, "building": Building}


class RelationshipService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def query(self, query: ExploreQuery, version: int) -> ExploreResult:
        agg = query.agg or "pairs"
        if agg not in AGGS:
            raise HTTPException(status_code=422, detail=f"agg must be one of {AGGS}")
        grain = query.grain or "hour"
        filter = parse_filter(query.filter)
        if agg == "matrix":
            slugs = query.parameters
            if len(slugs) < 2:
                raise HTTPException(
                    status_code=422, detail="matrix needs 2+ parameters"
                )
        else:
            if not query.x or not query.y:
                raise HTTPException(status_code=422, detail="pairs needs x and y")
            slugs = [query.x] + ([] if query.y in METRICS else [query.y])
        parameters = await check_parameters(self.session, sorted(set(slugs)))
        specs = resolve(query.by, grain)
        if grain == "raw":
            await check_raw_cap(self.session, filter, slugs)
        if agg == "matrix":
            buckets = await self._matrix(grain, query, filter, slugs)
            grain_label = grain
        elif query.y in METRICS:
            buckets = await self._metric_pairs(grain, query, filter, specs)
            grain_label = "space"
        else:
            buckets = await self._pairs(grain, query, filter, specs)
            grain_label = grain
        meta = Meta(
            source="relationships",
            agg=agg,
            grain=grain_label,
            dimensions=[s.key for s in specs],
            parameters=slugs,
            unit=common_unit(parameters),
            **{"from": query.from_},
            to=query.to,
            n=0,
            version=version,
        )
        return await finish(self.session, query, filter, meta, buckets, specs)

    def _paired(self, grain: str, query: ExploreQuery, filter: dict):
        """Self-join: x readings as `a`, y readings as `b`, matched on
        dataset, space and time (and instrument at raw)."""
        a, b = Fact(grain, "a"), Fact(grain, "b")
        on = [
            a.c.dataset_id == b.c.dataset_id,
            a.c.space_id == b.c.space_id,
            a.time == b.time,
        ]
        if grain == "raw":
            on.append(a.c.instrument_id == b.c.instrument_id)
        frame = a.frame()
        frame.select_from = a.table.join(b.table, and_(*on))
        return a, b, frame

    async def _pairs(self, grain, query, filter, specs) -> list[Bucket]:
        a, b, frame = self._paired(grain, query, filter)
        keys = [spec.column(frame) for spec in specs]
        x, y = a.value, b.value
        fit = select(
            *keys,
            func.count(),
            func.regr_slope(y, x),
            func.regr_intercept(y, x),
            func.regr_r2(y, x),
            func.corr(y, x),
        )
        fit = self._pair_where(fit, a, b, query, filter)
        fit = fit.select_from(frame.select_from).group_by(*keys)
        rows = [r for r in (await self.session.exec(fit)).all() if r[len(keys)]]
        width = len(keys)
        buckets = {
            tuple(key_text(v) for v in row[:width]): Bucket(
                key=[key_text(v) for v in row[:width]],
                n=int(row[width]),
                fit=Fit(
                    slope=number(row[width + 1]),
                    intercept=number(row[width + 2]),
                    r2=number(row[width + 3]),
                    r=number(row[width + 4]),
                ),
                points=[],
            )
            for row in rows
        }
        total = sum(bucket.n for bucket in buckets.values())
        step = max(1, math.ceil(total / SAMPLE))
        order = [a.c.dataset_id, a.c.space_id, a.time]
        numbered = select(
            *keys,
            x.label("x"),
            y.label("y"),
            func.row_number().over(order_by=order).label("rn"),
        )
        numbered = self._pair_where(numbered, a, b, query, filter)
        sub = numbered.select_from(frame.select_from).subquery()
        points = select(*sub.c).where((sub.c.rn - 1) % step == 0)
        for row in (await self.session.exec(points)).all():
            key = tuple(key_text(v) for v in row[:width])
            buckets[key].points.append((float(row[width]), float(row[width + 1])))
        for bucket in buckets.values():
            bucket.sampled = step > 1
        return list(buckets.values())

    def _pair_where(self, statement, a: Fact, b: Fact, query, filter):
        statement = a.where(statement, query, filter, [query.x])
        return statement.where(b.c.parameter == query.y)

    async def _metric_pairs(self, grain, query, filter, specs) -> list[Bucket]:
        """x aggregated per (dataset, space), then joined to the catalog
        column named by y: one point per space, the fit over all spaces."""
        entity, attr = query.y.split(".")
        fact = Fact(grain)
        inner = select(
            fact.c.dataset_id.label("dataset_id"),
            fact.c.space_id.label("space_id"),
            fact.c.building_id.label("building_id"),
            (
                func.sum(fact.value * fact.n) / func.sum(fact.n)
                if fact.n is not None
                else func.avg(fact.value)
            ).label("x"),
        )
        inner = fact.where(inner, query, filter, [query.x])
        inner = inner.where(fact.c.space_id.isnot(None))
        sub = inner.group_by(
            fact.c.dataset_id, fact.c.space_id, fact.c.building_id
        ).subquery()
        metric = getattr(METRIC_MODELS[entity], attr)
        joined = sub.join(Space, col(Space.id) == sub.c.space_id).outerjoin(
            Building, col(Building.id) == sub.c.building_id
        )
        # dimensions on the point's own space and building
        keys = []
        for spec in specs:
            if spec.entity not in ("space", "building"):
                raise HTTPException(
                    status_code=422, detail=f"'{spec.key}' cannot group metric pairs"
                )
            keys.append(getattr(METRIC_MODELS[spec.entity], attr_of(spec)))
        y = col(metric)
        base = (
            select(
                *keys,
                func.count(),
                func.regr_slope(y, sub.c.x),
                func.regr_intercept(y, sub.c.x),
                func.regr_r2(y, sub.c.x),
                func.corr(y, sub.c.x),
            )
            .select_from(joined)
            .where(y.isnot(None))
        )
        rows = [
            r
            for r in (await self.session.exec(base.group_by(*keys))).all()
            if r[len(keys)]
        ]
        width = len(keys)
        buckets = {
            tuple(key_text(v) for v in row[:width]): Bucket(
                key=[key_text(v) for v in row[:width]],
                n=int(row[width]),
                fit=Fit(
                    slope=number(row[width + 1]),
                    intercept=number(row[width + 2]),
                    r2=number(row[width + 3]),
                    r=number(row[width + 4]),
                ),
                points=[],
                sampled=False,
            )
            for row in rows
        }
        points = select(*keys, sub.c.x, y).select_from(joined).where(y.isnot(None))
        for row in (
            await self.session.exec(points.order_by(sub.c.dataset_id, sub.c.space_id))
        ).all():
            key = tuple(key_text(v) for v in row[:width])
            buckets[key].points.append((float(row[width]), float(row[width + 1])))
        return list(buckets.values())

    async def _matrix(self, grain, query, filter, slugs) -> list[Bucket]:
        """One scan: pivot the filtered rows to one column per parameter
        per (dataset, space, time), then correlate every pair."""
        if query.by:
            raise HTTPException(status_code=422, detail="matrix takes no `by`")
        fact = Fact(grain)
        columns = [
            func.max(fact.value).filter(fact.c.parameter == slug).label(f"p{i}")
            for i, slug in enumerate(slugs)
        ]
        pivot = select(fact.c.dataset_id, fact.c.space_id, fact.time, *columns)
        pivot = fact.where(pivot, query, filter, slugs)
        pivot = pivot.group_by(fact.c.dataset_id, fact.c.space_id, fact.time).cte(
            "pivot"
        )
        source = pivot
        if query.method == "spearman":
            source = self._ranked(pivot, len(slugs))
        cells = []
        for i in range(len(slugs)):
            for j in range(i + 1, len(slugs)):
                a, b = source.c[f"p{i}"], source.c[f"p{j}"]
                if query.method == "spearman":
                    a, b = source.c[f"r{i}_{j}"], source.c[f"r{j}_{i}"]
                cells.append(func.count(a).filter(b.isnot(None)))
                cells.append(func.corr(a, b))
        row = (await self.session.exec(select(*cells).select_from(source))).one()
        buckets = []
        k = 0
        for i in range(len(slugs)):
            for j in range(i + 1, len(slugs)):
                n, r = int(row[k]), number(row[k + 1])
                k += 2
                buckets.append(
                    Bucket(
                        key=[slugs[i], slugs[j]],
                        n=n,
                        fit=Fit(slope=None, intercept=None, r2=None, r=r),
                    )
                )
        # a cell with no co-timed rows stays in a partial matrix (the grid
        # must be complete), but a matrix with no data at all is the empty
        # state of D3: no buckets, `available_parameters` filled
        if all(bucket.n == 0 for bucket in buckets):
            return []
        return buckets

    def _ranked(self, pivot, width: int):
        """Spearman: rank each parameter within the rows where the other
        parameter of the pair is present (ties get their lowest rank), and
        blank the rank wherever either value is missing."""
        values = [pivot.c[f"p{i}"] for i in range(width)]
        pairs = [(i, j) for i in range(width) for j in range(width) if i != j]
        ranks = [
            func.rank()
            .over(partition_by=pivot.c[f"p{j}"].isnot(None), order_by=pivot.c[f"p{i}"])
            .label(f"r{i}_{j}")
            for i, j in pairs
        ]
        ranked = select(*values, *ranks).select_from(pivot).cte("ranked")
        masked = [
            case(
                (
                    and_(ranked.c[f"p{i}"].isnot(None), ranked.c[f"p{j}"].isnot(None)),
                    ranked.c[f"r{i}_{j}"],
                ),
                else_=None,
            ).label(f"r{i}_{j}")
            for i, j in pairs
        ]
        return (
            select(*[ranked.c[f"p{i}"] for i in range(width)], *masked)
            .select_from(ranked)
            .cte("masked")
        )


def attr_of(spec) -> str:
    """Catalog column behind a space/building dimension (its filter path)."""
    return spec.filter_path.split(".", 1)[1]
