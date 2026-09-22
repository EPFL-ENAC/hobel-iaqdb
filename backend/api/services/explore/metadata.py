"""`GET /stats/metadata`: group-by over catalog rows."""

from api.models.catalog import Building, Dataset, Space, Study
from api.models.explore import Availability, Bucket, ExploreQuery, ExploreResult, Meta
from api.models.measurement import DatasetParameter
from api.services.explore.dimensions import Frame, resolve
from api.services.explore.envelope import (
    check_parameters,
    common_unit,
    finish,
    key_text,
)
from api.services.explore.filters import apply_joined_filter, parse_filter
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

ROOTS = {"studies": Study, "buildings": Building, "spaces": Space, "datasets": Dataset}
ENTITY_OF = {"studies": "study", "buildings": "building", "spaces": "space", "datasets": "dataset"}
# columns a client never asks the availability of
IDENTITY_FIELDS = {"id", "identifier", "study_id", "building_id", "dataset_id", "folder"}


def metadata_frame(entity: str) -> Frame:
    """Join paths from each root entity to the others (study is the hub)."""
    parameter = (DatasetParameter, col(DatasetParameter.dataset_id) == col(Dataset.id), ("dataset",))
    if entity == "studies":
        available = {
            "building": (Building, col(Building.study_id) == col(Study.id), ()),
            "space": (Space, col(Space.study_id) == col(Study.id), ()),
            "dataset": (Dataset, col(Dataset.study_id) == col(Study.id), ()),
            "parameter": parameter,
        }
    elif entity == "buildings":
        available = {
            "study": (Study, col(Study.id) == col(Building.study_id), ()),
            "space": (Space, col(Space.building_id) == col(Building.id), ()),
            "dataset": (Dataset, col(Dataset.study_id) == col(Building.study_id), ()),
            "parameter": parameter,
        }
    elif entity == "spaces":
        available = {
            "building": (Building, col(Building.id) == col(Space.building_id), ()),
            "study": (Study, col(Study.id) == col(Space.study_id), ()),
            "dataset": (Dataset, col(Dataset.study_id) == col(Space.study_id), ()),
            "parameter": parameter,
        }
    else:
        available = {
            "study": (Study, col(Study.id) == col(Dataset.study_id), ()),
            "building": (Building, col(Building.study_id) == col(Dataset.study_id), ()),
            "space": (Space, col(Space.study_id) == col(Dataset.study_id), ()),
            "parameter": (DatasetParameter, col(DatasetParameter.dataset_id) == col(Dataset.id), ()),
        }
    frame = Frame(ENTITY_OF[entity], ROOTS[entity], available)
    frame.parameter = None
    return frame


def _parameter_column(frame: Frame):
    return col(frame.use("parameter").parameter)


class MetadataService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def query(self, query: ExploreQuery, version: int) -> ExploreResult:
        if query.entity is None:
            raise HTTPException(status_code=422, detail="entity is required")
        agg = query.agg or "count"
        if agg not in ("count", "availability"):
            raise HTTPException(status_code=422, detail="agg must be count or availability")
        filter = parse_filter(query.filter)
        parameters = await check_parameters(self.session, query.parameters)
        if agg == "availability":
            buckets, specs = await self._availability(query, filter)
        else:
            buckets, specs = await self._count(query, filter)
        meta = Meta(
            source="metadata",
            agg=agg,
            grain="entity",
            dimensions=[s.key for s in specs],
            parameters=query.parameters,
            unit=common_unit(parameters),
            **{"from": query.from_},
            to=query.to,
            n=0,
            version=version,
        )
        return await finish(self.session, query, filter, meta, buckets, specs)

    async def _count(self, query: ExploreQuery, filter: dict):
        specs = resolve(query.by, None)
        frame = metadata_frame(query.entity)
        frame.parameter = None
        root = ROOTS[query.entity]
        keys = []
        for spec in specs:
            if spec.key == "parameter":
                keys.append(_parameter_column(frame))
            else:
                keys.append(spec.column(frame))
        statement = select(*keys, func.count(func.distinct(root.id)))
        statement = apply_joined_filter(frame, statement, filter)
        if query.parameters:
            statement = statement.where(_parameter_column(frame).in_(query.parameters))
        statement = statement.select_from(frame.select_from).group_by(*keys)
        rows = (await self.session.exec(statement)).all()
        buckets = [
            Bucket(key=[key_text(v) for v in row[:-1]], n=int(row[-1])) for row in rows
        ]
        return buckets, specs

    async def _availability(self, query: ExploreQuery, filter: dict):
        if query.by:
            raise HTTPException(status_code=422, detail="availability takes no `by`")
        root = ROOTS[query.entity]
        fields = query.fields or nullable_fields(root)
        unknown = [f for f in fields if f not in root.model_fields]
        if unknown:
            raise HTTPException(status_code=422, detail=f"unknown fields {unknown}")
        frame = metadata_frame(query.entity)
        statement = select(
            func.count(func.distinct(root.id)),
            *[func.count(func.distinct(root.id)).filter(getattr(root, f).isnot(None)) for f in fields],
        )
        statement = apply_joined_filter(frame, statement, filter)
        if query.parameters:
            statement = statement.where(_parameter_column(frame).in_(query.parameters))
        statement = statement.select_from(frame.select_from)
        row = (await self.session.exec(statement)).one()
        total = int(row[0])
        buckets = [
            Bucket(
                key=[field],
                n=int(present),
                availability=Availability(present=int(present), total=total),
            )
            for field, present in zip(fields, row[1:])
        ]
        return buckets, []


def nullable_fields(model) -> list[str]:
    return [
        name
        for name, info in model.model_fields.items()
        if name not in IDENTITY_FIELDS and not info.is_required()
    ]
