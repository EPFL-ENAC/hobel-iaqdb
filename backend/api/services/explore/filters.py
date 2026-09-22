"""The catalog filter dialect (enacit4r-sql JSON, shared with /catalog/*),
anchored on the study: `{ ...study criteria, "$building": {...},
"$space": {...}, "$dataset": {...} }`.

Metadata queries apply the criteria on joined catalog tables; measurement
queries turn each block into an `id IN (subquery)` on the fact table, so the
fact scan never joins the catalog for filtering."""

from api.models.catalog import Building, Dataset, Space, Study
from api.services.explore.dimensions import Frame
from enacit4r_sql.utils.query import QueryBuilder, paramAsDict
from fastapi import HTTPException
from sqlmodel import select

NESTED = {"$building": "building", "$space": "space", "$dataset": "dataset"}
MODELS = {"study": Study, "building": Building, "space": Space, "dataset": Dataset}


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
