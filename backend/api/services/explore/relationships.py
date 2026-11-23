"""`GET /stats/relationships`: pairwise queries over co-located, co-timed
measurements (same dataset, space and time bucket)."""

import math
import statistics
from collections import defaultdict
from itertools import combinations

from api.models.catalog import Building, Space, Study
from api.models.explore import (
    Bucket,
    ExploreQuery,
    ExploreResult,
    Fit,
    Meta,
    StudyFit,
    Within,
)
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
from sqlalchemy import and_, case, func, literal, text, tuple_, union_all
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

AGGS = ("pairs", "matrix", "partners", "partnered")
# points a pairs chart gets at most; the fit is always over every row
SAMPLE = 2000
# memory a Spearman matrix sorts in, for its rank query only
SORT_MEMORY = "64MB"
METRIC_MODELS = {"space": Space, "building": Building}
# below these a correlation is noise (r = 0.00 from one point, #226): the
# bucket keeps its counts and points but gets no r and no fit
MIN_SPACES = 3
MIN_PAIRS = 30


def enough(n_pairs: int, n_spaces: int) -> bool:
    """Paired readings: enough pairs, over enough spaces."""
    return n_pairs >= MIN_PAIRS and n_spaces >= MIN_SPACES


def fit_bucket(row, width: int, n_spaces: int, reached: bool) -> Bucket:
    """A pairs bucket from (*keys, n, slope, intercept, r2, r, ...)."""
    slope, intercept, r2, r = (
        number(v) if reached else None for v in row[width + 1 : width + 5]
    )
    return Bucket(
        key=[key_text(v) for v in row[:width]],
        n=int(row[width]),
        n_spaces=n_spaces,
        enough=reached,
        fit=Fit(slope=slope, intercept=intercept, r2=r2, r=r),
        points=[],
    )


def by_study(group, study):
    """GROUP BY the keys, then the keys and the study: one scan gives the
    pooled row of each key and one row per study under it, told apart by
    `grouping(study)` (1 on the pooled row, where the study is not grouped)."""
    return func.grouping_sets(tuple_(*group), tuple_(*group, study))


def within(cells: list[tuple], reached, identifiers: dict[int, str]) -> Within:
    """`within` from the (study_id, n, n_spaces, r) row of each study with
    pairs. A study has an r if it reaches the minimum sample size alone,
    `reached(n, n_spaces)`, and if neither variable is constant in it."""
    studies = []
    for study, n, n_spaces, r in cells:
        alone = reached(int(n), int(n_spaces))
        studies.append(
            StudyFit(
                study=identifiers[study],
                n=int(n),
                n_spaces=int(n_spaces),
                enough=alone,
                r=number(r) if alone else None,
            )
        )
    studies.sort(key=lambda s: (0, s.r) if s.r is not None else (1, -s.n))
    rs = [s.r for s in studies if s.r is not None]
    return Within(median=statistics.median(rs) if rs else None, studies=studies)


async def add_studies(session: AsyncSession, buckets: dict, studies: dict, reached):
    """Set `n_studies` and `within` on each bucket from the (study_id, n,
    n_spaces, r) rows of its studies, both by the same key. A study with
    pairs counts: counting its rows costs no count(distinct), which sorts
    every row again. One lookup names the studies."""
    studies = {key: [c for c in cells if c[1]] for key, cells in studies.items()}
    ids = {cell[0] for cells in studies.values() for cell in cells}
    named = select(Study.id, Study.identifier).where(col(Study.id).in_(ids))
    identifiers = dict((await session.exec(named)).all()) if ids else {}
    for key, bucket in buckets.items():
        cells = studies.get(key, [])
        bucket.n_studies = len(cells)
        bucket.within = within(cells, reached, identifiers)


def fit_buckets(rows, width: int, reached) -> tuple[dict, dict]:
    """Pairs buckets from `by_study` rows (*keys, n, slope, intercept, r2, r,
    n_spaces, study_id, grouping): the pooled rows are the buckets, by key;
    the study rows are their (study_id, n, n_spaces, r), by the same key,
    for `add_studies`. `reached` is the minimum sample size."""
    buckets: dict[tuple, Bucket] = {}
    studies: dict[tuple, list[tuple]] = defaultdict(list)
    for row in rows:
        n, r, n_spaces = int(row[width]), row[width + 4], int(row[width + 5])
        # no group by: the pooled row of an empty scan counts 0
        if not n:
            continue
        key = tuple(key_text(v) for v in row[:width])
        if row[width + 7]:
            buckets[key] = fit_bucket(row, width, n_spaces, reached(n, n_spaces))
        else:
            studies[key].append((row[width + 6], n, n_spaces, r))
    return buckets, studies


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
        x, y, study = a.value, b.value, a.c.study_id
        fit = select(
            *keys,
            func.count(),
            func.regr_slope(y, x),
            func.regr_intercept(y, x),
            func.regr_r2(y, x),
            func.corr(y, x),
            func.count(a.c.space_id.distinct()),
            study,
            func.grouping(study),
        )
        fit = self._pair_where(fit, a, b, query, filter)
        fit = fit.select_from(frame.select_from).group_by(by_study(keys, study))
        width = len(keys)
        rows = (await self.session.exec(fit)).all()
        buckets, studies = fit_buckets(rows, width, enough)
        await add_studies(self.session, buckets, studies, enough)
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
            # a dataset is in one study: grouping by it splits no point
            fact.c.study_id.label("study_id"),
            (
                func.sum(fact.value * fact.n) / func.sum(fact.n)
                if fact.n is not None
                else func.avg(fact.value)
            ).label("y"),
        )
        inner = fact.where(inner, query, filter, [query.y])
        inner = inner.where(fact.c.space_id.isnot(None))
        sub = inner.group_by(
            fact.c.dataset_id, fact.c.space_id, fact.c.building_id, fact.c.study_id
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
                func.count(sub.c.space_id.distinct()),
                sub.c.study_id,
                func.grouping(sub.c.study_id),
            )
            .select_from(joined)
            .where(x.isnot(None))
            .group_by(by_study(keys, sub.c.study_id))
        )
        width = len(keys)

        def reached(n: int, n_spaces: int) -> bool:
            # one point per space: the spaces are the sample
            return n_spaces >= MIN_SPACES

        buckets, studies = fit_buckets(
            (await self.session.exec(base)).all(), width, reached
        )
        await add_studies(self.session, buckets, studies, reached)
        for bucket in buckets.values():
            bucket.sampled = False
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
        # a dataset is in one study: grouping by it splits no row
        pivot = select(
            fact.c.dataset_id, fact.c.space_id, fact.c.study_id, fact.time, *columns
        )
        pivot = fact.where(pivot, query, filter, slugs)
        pivot = pivot.group_by(
            fact.c.dataset_id, fact.c.space_id, fact.c.study_id, fact.time
        ).cte("pivot")
        pairs = list(combinations(range(len(slugs)), 2))
        # per pair, (n, n_spaces, r) of the pool, (study_id, n, n_spaces, r)
        # of each study
        pooled: dict[tuple[int, int], tuple] = {}
        studies: dict[tuple[int, int], list[tuple]] = defaultdict(list)

        def add(pair, pooled_row, study, *cell):
            if pooled_row:
                pooled[pair] = cell
            else:
                studies[pair].append((study, *cell))

        if query.method == "spearman":
            # the rank sorts spill to disk at the default work_mem
            await self.session.exec(text(f"SET LOCAL work_mem = '{SORT_MEMORY}'"))
            rows = (await self.session.exec(self._ranked(pivot, pairs))).all()
            # back to the default for the rest of the request: a savepoint
            # would not do, as releasing it keeps a SET LOCAL (on an error the
            # rollback drops it)
            await self.session.exec(text("RESET work_mem"))
            for i, j, pooled_row, study, *cell in rows:
                add((i, j), pooled_row, study, *cell)
        else:
            stats = []
            for i, j in pairs:
                a, b = pivot.c[f"p{i}"], pivot.c[f"p{j}"]
                both = and_(a.isnot(None), b.isnot(None))
                stats.append(func.count(a).filter(b.isnot(None)))
                stats.append(func.count(pivot.c.space_id.distinct()).filter(both))
                stats.append(func.corr(a, b))
            study = pivot.c.study_id
            statement = (
                select(*stats, study, func.grouping(study))
                .select_from(pivot)
                .group_by(by_study([], study))
            )
            for row in (await self.session.exec(statement)).all():
                for k, pair in enumerate(pairs):
                    add(pair, row[-1], row[-2], *row[3 * k : 3 * k + 3])
        buckets = {}
        for i, j in pairs:
            n, n_spaces, r = pooled[(i, j)]
            reached = enough(n, n_spaces)
            buckets[(i, j)] = Bucket(
                key=[slugs[i], slugs[j]],
                n=int(n),
                n_spaces=int(n_spaces),
                enough=reached,
                fit=Fit(
                    slope=None,
                    intercept=None,
                    r2=None,
                    r=number(r) if reached else None,
                ),
            )
        # a cell with no co-timed rows stays in a partial matrix (the grid
        # must be complete), but a matrix with no data at all is the empty
        # state of D3: no buckets, `available_parameters` filled
        if all(bucket.n == 0 for bucket in buckets.values()):
            return []
        await add_studies(self.session, buckets, studies, enough)
        return list(buckets.values())

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
        counts = select(
            shared.c.parameter, func.count(), func.count(shared.c.space_id.distinct())
        ).group_by(shared.c.parameter)
        rows = (await self.session.exec(counts)).all()
        return [
            Bucket(key=[slug], n=int(n), n_spaces=int(s), enough=enough(n, s))
            for slug, n, s in rows
        ]

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
            select(
                spaces.c.parameter,
                func.count(),
                func.count(spaces.c.space_id.distinct()),
            )
            .select_from(joined)
            .where(col(metric).isnot(None))
            .group_by(spaces.c.parameter)
        )
        rows = (await self.session.exec(counts)).all()
        # one point per space, as in the metric pairs
        return [
            Bucket(key=[slug], n=int(n), n_spaces=int(s), enough=s >= MIN_SPACES)
            for slug, n, s in rows
        ]

    def _ranked(self, pivot, pairs: list[tuple[int, int]]):
        """Spearman: per pair, rank both parameters within the rows where
        both are present and correlate the ranks. Ties get their average
        rank, as Spearman's rho requires: rank() is the lowest rank of a tie
        and cume_dist() times the row count its highest, both on the same
        sort. The pool ranks over every row of the pair, a study over its own
        rows: four sorts per pair. Per pair, one (i, j, grouping, study_id, n,
        n_spaces, r) row for the pool (grouping 1, no study), then one per
        study."""

        def average_rank(value, *partition):
            over = {"partition_by": partition or None, "order_by": value}
            lowest = func.rank().over(**over)
            highest = func.cume_dist().over(**over) * func.count().over(
                partition_by=partition or None
            )
            return (lowest + highest) / 2.0

        study = pivot.c.study_id
        cells = []
        for i, j in pairs:
            a, b = pivot.c[f"p{i}"], pivot.c[f"p{j}"]
            ranked = (
                select(
                    pivot.c.space_id,
                    study,
                    average_rank(a).label("a"),
                    average_rank(b).label("b"),
                    average_rank(a, study).label("study_a"),
                    average_rank(b, study).label("study_b"),
                )
                .where(a.isnot(None), b.isnot(None))
                .subquery()
            )
            pooled_row = func.grouping(ranked.c.study_id)
            cells.append(
                select(
                    literal(i),
                    literal(j),
                    pooled_row,
                    ranked.c.study_id,
                    func.count(),
                    func.count(ranked.c.space_id.distinct()),
                    case(
                        (pooled_row == 1, func.corr(ranked.c.a, ranked.c.b)),
                        else_=func.corr(ranked.c.study_a, ranked.c.study_b),
                    ),
                )
                .select_from(ranked)
                .group_by(by_study([], ranked.c.study_id))
            )
        return union_all(*cells)


def attr_of(spec) -> str:
    """Catalog column behind a space/building dimension (its filter path)."""
    return spec.filter_path.split(".", 1)[1]
