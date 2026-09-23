"""Shared pieces of the `{meta, buckets[]}` envelope: key formatting,
deterministic ordering, the empty state."""

from datetime import date, datetime
from decimal import Decimal

from api.models.explore import Bucket, ExploreQuery, ExploreResult, Meta
from api.models.measurement import Parameter
from api.services.explore.dimensions import DimensionSpec
from api.services.explore.filters import apply_fact_filter
from api.services.explore.tables import measurement_day
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


def key_text(value) -> str | None:
    """Bucket keys are strings (`"CH"`, `"2012-03-01"`, `"3"`) or null."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(int(value)) if value == int(value) else str(value)
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def order_buckets(buckets: list[Bucket], specs: list[DimensionSpec]) -> list[Bucket]:
    """Time dimensions ascending, category dimensions by n descending then
    key; nulls last. Same input, same order."""

    def sort_key(bucket: Bucket):
        parts = []
        for i, spec in enumerate(specs):
            key = bucket.key[i]
            if spec.kind == "time":
                parts.append((key is None, key or ""))
            else:
                parts.append((key is None, -bucket.n, key or ""))
        return parts

    return sorted(buckets, key=sort_key)


def number(value) -> float | None:
    return None if value is None else float(value)


async def check_parameters(
    session: AsyncSession, slugs: list[str]
) -> dict[str, Parameter]:
    """Known parameters by slug; an unknown slug is a 422 listing the valid ones."""
    known = {p.slug: p for p in (await session.exec(select(Parameter))).all()}
    unknown = [s for s in slugs if s not in known]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"unknown parameters {unknown}, expected one of {sorted(known)}",
        )
    return {s: known[s] for s in slugs}


def common_unit(parameters: dict[str, Parameter]) -> str | None:
    units = {p.unit for p in parameters.values()}
    return units.pop() if len(units) == 1 else None


async def available_parameters(
    session: AsyncSession, query: ExploreQuery, filter: dict
) -> list[str]:
    """Slugs that do have data under the same filter and time range: the
    empty-state suggestion. Read from the daily aggregate so building and
    space criteria apply to the rows themselves."""
    day = measurement_day
    statement = select(day.c.parameter).distinct()
    if query.from_:
        statement = statement.where(day.c.day >= query.from_)
    if query.to:
        statement = statement.where(day.c.day < query.to)
    statement = apply_fact_filter(day, statement, filter)
    return sorted((await session.exec(statement)).all())


async def finish(
    session: AsyncSession,
    query: ExploreQuery,
    filter: dict,
    meta: Meta,
    buckets: list[Bucket],
    specs: list[DimensionSpec],
):
    """Order the buckets, total the counts, fill the empty state."""
    buckets = order_buckets(buckets, specs)
    meta.n = sum(b.n for b in buckets)
    if any(b.n_records is not None for b in buckets):
        meta.n_records = sum(b.n_records or 0 for b in buckets)
    if not buckets:
        meta.available_parameters = await available_parameters(session, query, filter)
    return ExploreResult(meta=meta, buckets=buckets)
