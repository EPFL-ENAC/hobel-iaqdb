"""The catalog filter dialect (enacit4r-sql JSON, shared with /catalog/*),
anchored on the study: `{ ...study criteria, "$building": {...},
"$space": {...}, "$dataset": {...} }`.

Metadata queries apply the criteria on joined catalog tables; measurement
queries turn each block into an `id IN (subquery)` on the fact table, so the
fact scan never joins the catalog for filtering."""

from api.models.catalog import Building, Dataset, Space, Study
from api.services.explore.dimensions import KOPPEN_GROUPS, ZONE_GROUPS, Frame
from enacit4r_sql.utils.query import QueryBuilder, paramAsDict
from fastapi import HTTPException
from sqlalchemy import or_
from sqlmodel import select

NESTED = {"$building": "building", "$space": "space", "$dataset": "dataset"}
MODELS = {"study": Study, "building": Building, "space": Space, "dataset": Dataset}


def climate_group_clause(model, groups: list[str | None]):
    """Buildings with a zone of one of the groups; None, with no zone of the
    mapping (null or "NA"), as the climate_group dimension buckets them."""
    unknown = [g for g in groups if g is not None and g not in KOPPEN_GROUPS]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"unknown climate group {unknown}, expected one of"
            f" {sorted(KOPPEN_GROUPS)}",
        )
    zone = model.climate_zone
    zones = [z for g in groups if g is not None for z in KOPPEN_GROUPS[g]]
    clauses = [zone.in_(zones)] if zones else []
    if None in groups:
        clauses.append(or_(zone.is_(None), zone.not_in(list(ZONE_GROUPS))))
    return or_(*clauses)


# filter fields that are no column of the model: a clause per list of values
DERIVED_FIELDS = {Building: {"climate_group": climate_group_clause}}


def parse_filter(raw: str | None) -> dict:
    try:
        parsed = paramAsDict(raw)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"filter is not JSON: {e}")
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=422, detail="filter must be a JSON object")
    return parsed


def criteria_of(filter: dict) -> dict[str, dict]:
    """Non-empty criteria per entity: study (top level) and the nested blocks."""
    criteria = {}
    study = {k: v for k, v in filter.items() if k not in NESTED and v is not None}
    if study:
        criteria["study"] = study
    for key, entity in NESTED.items():
        block = filter.get(key)
        if isinstance(block, dict):
            block = {k: v for k, v in block.items() if v is not None}
            if block:
                criteria[entity] = block
    return criteria


def apply_criteria(statement, model, criteria: dict):
    derived = DERIVED_FIELDS.get(model, {})
    for field in [f for f in criteria if f in derived]:
        value = criteria[field]
        values = value if isinstance(value, list) else [value]
        statement = statement.where(derived[field](model, values))
    criteria = {f: v for f, v in criteria.items() if f not in derived}
    if not criteria:
        return statement
    builder = QueryBuilder(model, {}, [], [])
    try:
        return builder._apply_model_filter(statement, model, criteria)
    except AttributeError as e:
        raise HTTPException(
            status_code=422, detail=f"unknown filter field for {model.__name__}: {e}"
        )


def apply_joined_filter(frame: Frame, statement, filter: dict):
    """Metadata: WHERE clauses on the joined catalog entities."""
    for entity, criteria in criteria_of(filter).items():
        statement = apply_criteria(statement, frame.use(entity), criteria)
    return statement


def id_subquery(entity: str, criteria: dict):
    model = MODELS[entity]
    return apply_criteria(select(model.id), model, criteria)


def apply_fact_filter(fact, statement, filter: dict):
    """Measurements: `column IN (ids matching the block)` on the fact table."""
    columns = {
        "study": fact.c.study_id,
        "building": fact.c.building_id,
        "space": fact.c.space_id,
        "dataset": fact.c.dataset_id,
    }
    for entity, criteria in criteria_of(filter).items():
        statement = statement.where(columns[entity].in_(id_subquery(entity, criteria)))
    return statement
