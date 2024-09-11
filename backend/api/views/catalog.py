from typing import List
from fastapi import APIRouter, Security, Depends, Query
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from api.db import get_session, AsyncSession
from api.auth import get_api_key
from api.services.study import StudyService
from api.services.study_parser import StudyParser
from api.services.building import BuildingService
from api.services.space import SpaceService
from api.services.instrument import InstrumentService
from api.services.dataset import DatasetService
from api.models.catalog import Study, StudyRead, StudyDraft, StudiesResult, Building, BuildingRead, BuildingsResult, Space, SpacesResult, Instrument, InstrumentsResult, Dataset, DatasetsResult
from api.utils.query import paramAsArray, paramAsDict
from api.utils.file_size import size_checker

router = APIRouter()


@router.post("/study-excel",
             status_code=200,
             dependencies=[Depends(size_checker)],
             response_model=StudyDraft)
async def read_study_from_excel(
    files: UploadFile = File(
        description="Excel file containing study, building, space descriptions")):
    study = StudyParser().parse(files.file._file)
    return study


@router.get("/studies", response_model=StudiesResult)
async def get_studies(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> StudiesResult:
    """Get all studies"""
    service = StudyService(session)
    res = await service.find(paramAsDict(filter), paramAsArray(sort), paramAsArray(range))
    return res


@router.get("/study/{id}", response_model=StudyRead)
async def get_study(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> Study:
    """Get a study by id"""
    service = StudyService(session)
    res = await service.get(id)
    return res


@router.delete("/study/{id}")
async def delete_study(
    id: int,
    session: AsyncSession = Depends(get_session),
    api_key: str = Security(get_api_key),
) -> None:
    """Delete study by id"""
    service = StudyService(session)
    await service.delete(id)


@router.get("/study/{id}/buildings", response_model=BuildingsResult)
async def get_study_buildings(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> BuildingsResult:
    """Get a study buildings by id"""
    service = BuildingService(session)
    res = await service.find({"study_id": id}, [], [])
    return res


@router.get("/study/{id}/spaces", response_model=SpacesResult)
async def get_study_spaces(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> SpacesResult:
    """Get a study spaces by id"""
    service = SpaceService(session)
    res = await service.find({"study_id": id}, [], [])
    return res


@router.get("/study/{id}/building/{building_id}/spaces", response_model=SpacesResult)
async def get_study_building_spaces(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
    building_id: int,
) -> SpacesResult:
    """Get a study spaces by id"""
    service = SpaceService(session)
    res = await service.find({"study_id": id, "building_id": building_id}, [], [])
    return res


@router.get("/study/{id}/instruments", response_model=InstrumentsResult)
async def get_study_instruments(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> InstrumentsResult:
    """Get a study instruments by id"""
    service = InstrumentService(session)
    res = await service.find({"study_id": id}, [], [])
    return res


@router.get("/study/{id}/datasets", response_model=DatasetsResult)
async def get_study_datasets(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> DatasetsResult:
    """Get a study instruments by id"""
    service = DatasetService(session)
    res = await service.find({"study_id": id}, [], [])
    return res


@router.get("/buildings", response_model=BuildingsResult)
async def get_buildings(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> BuildingsResult:
    """Get all buildings"""
    service = BuildingService(session)
    res = await service.find(paramAsDict(filter), paramAsArray(sort), paramAsArray(range))
    return res


@router.get("/building/{id}", response_model=BuildingRead)
async def get_building(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> Building:
    """Get a building by id"""
    service = BuildingService(session)
    res = await service.get(id)
    return res


@router.delete("/building/{id}")
async def delete_building(
    id: int,
    session: AsyncSession = Depends(get_session),
    api_key: str = Security(get_api_key),
) -> None:
    """Delete building by id"""
    service = BuildingService(session)
    await service.delete(id)


@router.get("/spaces", response_model=SpacesResult)
async def get_spaces(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> SpacesResult:
    """Get all spaces"""
    service = SpaceService(session)
    res = await service.find(paramAsDict(filter), paramAsArray(sort), paramAsArray(range))
    return res


@router.get("/space/{id}", response_model=Space)
async def get_space(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> Space:
    """Get a space by id"""
    service = SpaceService(session)
    res = await service.get(id)
    return res


@router.delete("/space/{id}")
async def delete_space(
    id: int,
    session: AsyncSession = Depends(get_session),
    api_key: str = Security(get_api_key),
) -> None:
    """Delete space by id"""
    service = SpaceService(session)
    await service.delete(id)


@router.get("/instruments", response_model=InstrumentsResult)
async def get_instruments(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> InstrumentsResult:
    """Get all instruments"""
    service = InstrumentService(session)
    res = await service.find(paramAsDict(filter), paramAsArray(sort), paramAsArray(range))
    return res


@router.get("/instrument/{id}", response_model=Instrument)
async def get_instrument(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> Instrument:
    """Get an instrument by id"""
    service = InstrumentService(session)
    res = await service.get(id)
    return res


@router.get("/datasets", response_model=DatasetsResult)
async def get_datasets(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> DatasetsResult:
    """Get all datasets"""
    service = DatasetService(session)
    res = await service.find(paramAsDict(filter), paramAsArray(sort), paramAsArray(range))
    return res


@router.get("/dataset/{id}", response_model=Dataset)
async def get_dataset(
    session: AsyncSession = Depends(get_session),
    *,
    id: int,
) -> Dataset:
    """Get a dataset by id"""
    service = DatasetService(session)
    res = await service.get(id)
    return res
