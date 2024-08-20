from typing import List
from fastapi import APIRouter, Depends, Query
from api.db import get_session, AsyncSession
from api.auth import get_api_key
from api.services.study import StudyService
from api.services.building import BuildingService
from api.models.catalog import Study, StudyRead, StudiesResult, Building, BuildingRead, BuildingsResult
from api.utils.query import paramAsArray, paramAsObject

router = APIRouter()


@router.get("/study/{id}", response_model=StudyRead)
async def getStudy(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> Study:
    """Get a study by id"""
    service = StudyService(session)
    study = await service.get(id)
    return study


@router.get("/studies", response_model=StudiesResult)
async def getStudies(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> StudiesResult:
    """Get all studies"""
    service = StudyService(session)
    studies = await service.find(paramAsObject(filter), paramAsArray(sort), paramAsArray(range))
    return studies


@router.get("/building/{id}", response_model=BuildingRead)
async def getBuilding(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> Building:
    """Get a building by id"""
    service = BuildingService(session)
    building = await service.get(id)
    return building


@router.get("/buildings", response_model=BuildingsResult)
async def getBuildings(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> StudiesResult:
    """Get all buildings"""
    service = BuildingService(session)
    buildings = await service.find(paramAsObject(filter), paramAsArray(sort), paramAsArray(range))
    return buildings
