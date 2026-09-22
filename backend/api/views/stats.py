"""Explore charts API: one static descriptor and three query-shaped routes
sharing one parameter contract and one response envelope
(docs/129-explore-charts-api.md)."""

from typing import Annotated

from api.db import AsyncSession, get_session
from api.models.explore import ExploreQuery, ExploreResult, ExploreSchema
from api.services.catalog_version import CatalogVersionService
from api.services.explore.cache import canonical_key, respond
from api.services.explore.metadata import MetadataService
from api.services.explore.schema import explore_schema
from fastapi import APIRouter, Depends, Query, Request

router = APIRouter()


@router.get("/schema", response_model=ExploreSchema)
async def get_schema(request: Request, session: AsyncSession = Depends(get_session)):
    """Dimensions, parameter dictionary with benchmarks, metrics and the
    catalog version; load once, long-cached."""
    version = await CatalogVersionService(session).get()
    key = canonical_key("schema", None, version)
    return await respond(request, key, lambda: explore_schema(session, version))


@router.get("/metadata", response_model=ExploreResult, response_model_exclude_none=True)
async def get_metadata(
    request: Request,
    query: Annotated[ExploreQuery, Query()],
    session: AsyncSession = Depends(get_session),
):
    """Group-by over catalog rows: `agg=count` (default) counts distinct
    entities per key, `agg=availability` gives `{present, total}` per field."""
    version = await CatalogVersionService(session).get()
    key = canonical_key("metadata", query, version)
    service = MetadataService(session)
    return await respond(request, key, lambda: service.query(query, version))
