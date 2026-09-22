from api.auth import User, kc_service
from api.db import AsyncSession, get_engine, get_session
from api.models.catalog import (
    Building,
    BuildingRead,
    BuildingsResult,
    Dataset,
    DatasetsResult,
    Instrument,
    InstrumentsResult,
    Space,
    SpacesResult,
    StudiesResult,
    Study,
    StudyRead,
    StudySummariesResult,
    StudySummary,
)
from api.services.building import BuildingService
from api.services.catalog_version import CatalogVersionService
from api.services.dataset import DatasetService
from api.services.instrument import InstrumentService
from api.services.publish import refresh_after_delete
from api.services.space import SpaceService
from api.services.study import StudyService
from api.utils.colors import string_to_color
from enacit4r_sql.utils.query import paramAsArray, paramAsDict
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncEngine

router = APIRouter()


async def _published_data_changed(
    session: AsyncSession, engine: AsyncEngine, background_tasks: BackgroundTasks
) -> None:
    """Invalidate the explore caches and bring the continuous aggregates in
    line with the cascaded measurement deletes."""
    await CatalogVersionService(session).bump()
    await session.commit()
    background_tasks.add_task(refresh_after_delete, engine)


@router.get("/study-summaries", response_model=StudySummariesResult)
async def get_study_summaries(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> StudySummariesResult:
    """Get all study summaries"""
    service = StudyService(session)
    res = await service.find(
        paramAsDict(filter), paramAsArray(sort), paramAsArray(range)
    )
    if res is None:
        return StudySummariesResult(studies=[])
    # Make study summary from study
    summaries = [
        StudySummary(
            id=study.id,
            identifier=study.identifier,
            name=study.name,
            description=study.description,
            countries=list(set([building.country for building in study.buildings])),
            cities=list(
                set(
                    [
                        f"{building.city}, {building.country}"
                        for building in study.buildings
                        if building.city and building.country
                    ]
                )
            ),
            color=string_to_color(study.identifier),
        )
        for study in res.data
    ]
    return StudySummariesResult(
        data=summaries, total=res.total, skip=res.skip, limit=res.limit
    )


@router.get("/studies", response_model=StudiesResult)
async def get_studies(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> StudiesResult:
    """Get all studies"""
    service = StudyService(session)
    res = await service.find(
        paramAsDict(filter), paramAsArray(sort), paramAsArray(range)
    )
    return res


@router.get("/study/{id}", response_model=StudyRead)
async def get_study(
    session: AsyncSession = Depends(get_session),
    *,
    id: str,
) -> Study:
    """Get a study by id or identifier"""
    service = StudyService(session)
    if id.isdigit():
        res = await service.get(int(id))
    else:
        res = await service.get_by_identifier(id)
    return res


@router.delete("/study/{id}")
async def delete_study(
    id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    engine: AsyncEngine = Depends(get_engine),
    user: User = Depends(kc_service.require_admin()),
) -> None:
    """Delete study by id or identifier"""
    service = StudyService(session)
    if id.isdigit():
        await service.delete(int(id))
    else:
        await service.delete_by_identifier(id)
    await _published_data_changed(session, engine, background_tasks)


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
    res = await service.find(
        paramAsDict(filter), paramAsArray(sort), paramAsArray(range)
    )
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
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    engine: AsyncEngine = Depends(get_engine),
    user: User = Depends(kc_service.require_admin()),
) -> None:
    """Delete building by id"""
    service = BuildingService(session)
    await service.delete(id)
    await _published_data_changed(session, engine, background_tasks)


@router.get("/spaces", response_model=SpacesResult)
async def get_spaces(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> SpacesResult:
    """Get all spaces"""
    service = SpaceService(session)
    res = await service.find(
        paramAsDict(filter), paramAsArray(sort), paramAsArray(range)
    )
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
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    engine: AsyncEngine = Depends(get_engine),
    user: User = Depends(kc_service.require_admin()),
) -> None:
    """Delete space by id"""
    service = SpaceService(session)
    await service.delete(id)
    await _published_data_changed(session, engine, background_tasks)


@router.get("/instruments", response_model=InstrumentsResult)
async def get_instruments(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> InstrumentsResult:
    """Get all instruments"""
    service = InstrumentService(session)
    res = await service.find(
        paramAsDict(filter), paramAsArray(sort), paramAsArray(range)
    )
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
    res = await service.find(
        paramAsDict(filter), paramAsArray(sort), paramAsArray(range)
    )
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
