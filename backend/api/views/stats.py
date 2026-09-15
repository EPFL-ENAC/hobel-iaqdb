from api.db import AsyncSession, get_session
from api.models.catalog import GroupByResult
from api.services.building import BuildingService
from api.services.space import SpaceService
from api.services.study import StudyService
from enacit4r_sql.utils.query import paramAsDict
from fastapi import APIRouter, Depends, Query

router = APIRouter()


@router.get("/frequencies/studies")
async def count_studies(
    filter: str = Query(None),
    by: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> GroupByResult:
    """Count filtered studies grouped by a field"""
    service = StudyService(session)
    res = await service.count_group_by(paramAsDict(filter), by)
    return res


@router.get("/frequencies/buildings")
async def count_buildings(
    filter: str = Query(None),
    by: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> GroupByResult:
    """Count filtered buildings grouped by a field"""
    service = BuildingService(session)
    res = await service.count_group_by(paramAsDict(filter), by)
    return res


@router.get("/frequencies/spaces")
async def count_spaces(
    filter: str = Query(None),
    by: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> GroupByResult:
    """Count filtered spaces grouped by a field"""
    service = SpaceService(session)
    res = await service.count_group_by(paramAsDict(filter), by)
    return res
