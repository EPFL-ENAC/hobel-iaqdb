"""The fact side shared by measurement and relationship queries: which
table a grain reads, the FROM clause around it, the common WHERE clauses and
the raw-grain cap."""

from api.models.catalog import Building, Dataset, Space, Study
from api.models.explore import ExploreQuery
from api.models.measurement import DatasetParameter
from api.services.explore.dimensions import Frame
from api.services.explore.filters import apply_criteria, apply_fact_filter, criteria_of
from api.services.explore.tables import GRAIN_TABLES
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

# raw readings a single request may scan; above it the client falls back to hour
RAW_CAP = 20_000_000


class Fact:
    """A grain's table with its time and value columns, possibly aliased."""

    def __init__(self, grain: str, alias: str | None = None):
        table, time, value, n = GRAIN_TABLES[grain]
        self.grain = grain
        self.table = table.alias(alias) if alias else table
        self.time = self.table.c[time]
        self.value = self.table.c[value]
        # readings behind a row: 1 at raw, the bucket count otherwise
        self.n = self.table.c[n] if n else None
        self.c = self.table.c

    def frame(self) -> Frame:
        t = self.table
        available = {
            "study": (Study, col(Study.id) == t.c.study_id, ()),
            "building": (Building, col(Building.id) == t.c.building_id, ()),
            "space": (Space, col(Space.id) == t.c.space_id, ()),
            "dataset": (Dataset, col(Dataset.id) == t.c.dataset_id, ()),
        }
        return Frame("fact", t, available, time=self.time, parameter=t.c.parameter)

    def records(self):
        return func.sum(self.n) if self.n is not None else func.count()

    def where(
        self, statement, query: ExploreQuery, filter: dict, parameters: list[str]
    ):
        if parameters:
            statement = statement.where(self.c.parameter.in_(parameters))
        if query.from_:
            statement = statement.where(self.time >= query.from_)
        if query.to:
            statement = statement.where(self.time < query.to)
        if self.grain == "raw" and query.qualifier:
            statement = statement.where(self.c.value_qualifier.in_(query.qualifier))
        return apply_fact_filter(self.table, statement, filter)


async def check_raw_cap(
    session: AsyncSession, filter: dict, parameters: list[str]
) -> int:
    """Raw readings the filter can reach, from `dataset_parameter`; a
    request above the cap is refused with the count (no silent downgrade)."""
    cap = RAW_CAP
    statement = select(func.coalesce(func.sum(DatasetParameter.n_records), 0)).join(
        Dataset, col(Dataset.id) == col(DatasetParameter.dataset_id)
    )
    if parameters:
        statement = statement.where(col(DatasetParameter.parameter).in_(parameters))
    criteria = criteria_of(filter)
    if "dataset" in criteria:
        statement = apply_criteria(statement, Dataset, criteria["dataset"])
    if "study" in criteria:
        statement = statement.join(Study, col(Study.id) == col(Dataset.study_id))
        statement = apply_criteria(statement, Study, criteria["study"])
    matched = int((await session.exec(statement)).one())
    if matched > cap:
        raise HTTPException(
            status_code=422,
            detail=f"grain=raw covers {matched} records, above the cap of {cap};"
            " use grain=hour",
        )
    return matched
