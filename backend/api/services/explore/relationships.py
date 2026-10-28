"""`GET /stats/relationships`: pairwise queries over co-located, co-timed
measurements (same dataset, space and time bucket)."""

import math
from itertools import combinations

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
from sqlalchemy import and_, func, literal, text, union_all
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

AGGS = ("pairs", "matrix", "partners", "partnered")
# points a pairs chart gets at most; the fit is always over every row
SAMPLE = 2000
# memory a Spearman matrix sorts in, for its rank query only
SORT_MEMORY = "64MB"
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
        elif agg == "partners":
            if not query.x:
                raise HTTPException(
                    status_code=422, detail="partners needs a parameter or metric x"
                )
            slugs = [] if query.x in METRICS else [query.x]
        elif agg == "partnered":
            slugs = []
        else:
            if not query.x or not query.y:
                raise HTTPException(status_code=422, detail="pairs needs x and y")
            if query.y in METRICS:
                raise HTTPException(
                    status_code=422,
                    detail="a metric goes in x: y is fitted as a function of x",
                )
            slugs = ([] if query.x in METRICS else [query.x]) + [query.y]
        parameters = await check_parameters(self.session, sorted(set(slugs)))
        specs = resolve(query.by, grain)
        if grain == "raw":
            # partners scans every parameter, not only x
            scanned = [] if agg in ("partners", "partnered") else slugs
            await check_raw_cap(self.session, filter, scanned)
        if agg == "matrix":
            buckets = await self._matrix(grain, query, filter, slugs)
            grain_label = grain
        elif agg == "partners" and query.x in METRICS:
            buckets = await self._metric_partners(grain, query, filter)
            grain_label = "space"
        elif agg == "partners":
            buckets = await self._partners(grain, query, filter)
            grain_label = grain
        elif agg == "partnered":
            buckets = await self._partnered(grain, query, filter)
            grain_label = grain
        elif query.x in METRICS:
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
        """The catalog column named by x against y aggregated per (dataset,
        space): one point per space, y fitted on x over all spaces."""
        entity, attr = query.x.split(".")
        fact = Fact(grain)
        inner = select(
            fact.c.dataset_id.label("dataset_id"),
            fact.c.space_id.label("space_id"),
            fact.c.building_id.label("building_id"),
            (
                func.sum(fact.value * fact.n) / func.sum(fact.n)
                if fact.n is not None
                else func.avg(fact.value)
            ).label("y"),
        )
        inner = fact.where(inner, query, filter, [query.y])
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
        x, y = col(metric), sub.c.y
        base = (
            select(
                *keys,
                func.count(),
                func.regr_slope(y, x),
                func.regr_intercept(y, x),
                func.regr_r2(y, x),
                func.corr(y, x),
            )
            .select_from(joined)
            .where(x.isnot(None))
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
        points = select(*keys, x, y).select_from(joined).where(x.isnot(None))
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
        pairs = list(combinations(range(len(slugs)), 2))
        if query.method == "spearman":
            # the rank sorts spill to disk at the default work_mem
            await self.session.exec(text(f"SET LOCAL work_mem = '{SORT_MEMORY}'"))
            rows = (await self.session.exec(self._ranked(pivot, pairs))).all()
            # back to the default for the rest of the request: a savepoint
            # would not do, as releasing it keeps a SET LOCAL (on an error the
            # rollback drops it)
            await self.session.exec(text("RESET work_mem"))
            cells = {(i, j): (n, r) for i, j, n, r in rows}
        else:
            stats = []
            for i, j in pairs:
                a, b = pivot.c[f"p{i}"], pivot.c[f"p{j}"]
                stats.append(func.count(a).filter(b.isnot(None)))
                stats.append(func.corr(a, b))
            row = (await self.session.exec(select(*stats).select_from(pivot))).one()
            cells = {pair: row[2 * k : 2 * k + 2] for k, pair in enumerate(pairs)}
        buckets = []
        for i, j in pairs:
            n, r = cells[(i, j)]
            buckets.append(
                Bucket(
                    key=[slugs[i], slugs[j]],
                    n=int(n),
                    fit=Fit(slope=None, intercept=None, r2=None, r=number(r)),
                )
            )
        # a cell with no co-timed rows stays in a partial matrix (the grid
        # must be complete), but a matrix with no data at all is the empty
        # state of D3: no buckets, `available_parameters` filled
        if all(bucket.n == 0 for bucket in buckets):
            return []
        return buckets

    async def _partners(self, grain, query, filter) -> list[Bucket]:
        """The parameters measured with x: per parameter, the (dataset,
        space, time) rows it shares with x, as a matrix cell with x counts
        them. One statement, whatever the number of parameters."""
        if query.by:
            raise HTTPException(status_code=422, detail="partners takes no `by`")
        x, other = Fact(grain, "x"), Fact(grain, "other")
        with_x = x.where(
            select(x.c.dataset_id, x.c.space_id, x.time.label("time")),
            query,
            filter,
            [query.x],
        )
        with_x = with_x.distinct().subquery("with_x")
        shared = select(
            other.c.parameter, other.c.dataset_id, other.c.space_id, other.time
        ).join(
            with_x,
            and_(
                other.c.dataset_id == with_x.c.dataset_id,
                other.c.space_id == with_x.c.space_id,
                other.time == with_x.c.time,
            ),
        )
        shared = other.where(shared, query, filter, [])
        shared = shared.where(other.c.parameter != query.x).distinct().subquery()
        counts = select(shared.c.parameter, func.count()).group_by(shared.c.parameter)
        rows = (await self.session.exec(counts)).all()
        return [Bucket(key=[slug], n=int(n)) for slug, n in rows]

    async def _partnered(self, grain, query, filter) -> list[Bucket]:
        """The parameters measured with any other: per parameter, the
        (dataset, space, time) rows it shares with at least one. One scan
        for every parameter, where `partners` answers for one x."""
        if query.by:
            raise HTTPException(status_code=422, detail="partnered takes no `by`")
        fact = Fact(grain)
        distinct = fact.c.parameter.distinct()
        # per row measuring two parameters or more, one line per parameter
        shared = (
            select(func.unnest(func.array_agg(distinct)).label("slug"))
            .where(fact.c.space_id.isnot(None))
            .group_by(fact.c.dataset_id, fact.c.space_id, fact.time)
            .having(func.count(distinct) > 1)
        )
        shared = fact.where(shared, query, filter, []).subquery("shared")
        counts = select(shared.c.slug, func.count()).group_by(shared.c.slug)
        rows = (await self.session.exec(counts)).all()
        return [Bucket(key=[slug], n=int(n)) for slug, n in rows]

    async def _metric_partners(self, grain, query, filter) -> list[Bucket]:
        """The parameters measured with the catalog column x: per parameter,
        the spaces with x set it was measured in, the points of its metric
        pairs. One statement, whatever the number of parameters."""
        if query.by:
            raise HTTPException(status_code=422, detail="partners takes no `by`")
        entity, attr = query.x.split(".")
        fact = Fact(grain)
        spaces = select(
            fact.c.parameter, fact.c.dataset_id, fact.c.space_id, fact.c.building_id
        )
        spaces = fact.where(spaces, query, filter, [])
        spaces = spaces.where(fact.c.space_id.isnot(None)).distinct().subquery()
        metric = getattr(METRIC_MODELS[entity], attr)
        joined = spaces.join(Space, col(Space.id) == spaces.c.space_id).outerjoin(
            Building, col(Building.id) == spaces.c.building_id
        )
        counts = (
            select(spaces.c.parameter, func.count())
            .select_from(joined)
            .where(col(metric).isnot(None))
            .group_by(spaces.c.parameter)
        )
        rows = (await self.session.exec(counts)).all()
        return [Bucket(key=[slug], n=int(n)) for slug, n in rows]

    def _ranked(self, pivot, pairs: list[tuple[int, int]]):
        """Spearman: per pair, rank both parameters within the rows where
        both are present and correlate the ranks, one (i, j, n, r) row per
        pair. Ties get their average rank, as Spearman's rho requires:
        rank() is the lowest rank of a tie and cume_dist() times the row
        count its highest, both on the same sort, so a pair costs two sorts
        over its own rows only."""

        def average_rank(value):
            lowest = func.rank().over(order_by=value)
            highest = func.cume_dist().over(order_by=value) * func.count().over()
            return (lowest + highest) / 2.0

        cells = []
        for i, j in pairs:
            a, b = pivot.c[f"p{i}"], pivot.c[f"p{j}"]
            ranked = (
                select(average_rank(a).label("a"), average_rank(b).label("b"))
                .where(a.isnot(None), b.isnot(None))
                .subquery()
            )
            cells.append(
                select(
                    literal(i),
                    literal(j),
                    func.count(),
                    func.corr(ranked.c.a, ranked.c.b),
                ).select_from(ranked)
            )
        return union_all(*cells)


def attr_of(spec) -> str:
    """Catalog column behind a space/building dimension (its filter path)."""
    return spec.filter_path.split(".", 1)[1]
