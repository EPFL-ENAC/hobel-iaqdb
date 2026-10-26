from importlib.resources import files
from typing import Literal

from api.auth import User, kc_service
from api.config import config
from api.db import AsyncSession, get_engine, get_session
from api.models.catalog import (
    Contribution,
    ContributionsResult,
    DatasetLoadsResult,
    Study,
    StudyBundlesResult,
    StudyDraft,
    StudyDraftParseResult,
    StudyDraftsResult,
    StudyRead,
)
from api.services.catalog_version import CatalogVersionService
from api.services.contribution import ContributionService
from api.services.dataset import DatasetService
from api.services.publish import load_published_study
from api.services.study import StudyService
from api.services.study_draft import BundleSort, StudyDraftService
from api.services.study_parser import StudyParser
from api.utils.files import file_checker
from enacit4r_sql.utils.query import paramAsArray, paramAsDict
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from fastapi.responses import FileResponse, Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncEngine

router = APIRouter()


@router.get("/study-template")
async def get_study_template():
    version = "3.3.1"
    data_file_path = str(files("api") / f"data/Metadata_entry_form_v{version}.xlsm")
    return FileResponse(
        data_file_path,
        filename=f"iaqdb_study_template_v{version}.xlsm",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/dataset-dictionary")
async def get_dataset_dictionary():
    data_file_path = str(files("api") / "data/Dictionary_data.xlsx")
    return FileResponse(
        data_file_path,
        filename="iaqdb_dataset_dictionary.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post(
    "/study-excel",
    status_code=200,
    dependencies=[Depends(file_checker.check_size)],
    response_model=StudyDraftParseResult,
)
async def read_study_from_excel(
    files: UploadFile = File(
        description="Excel file containing study, building, space descriptions"
    ),
):
    try:
        parser = StudyParser()
        # parsing geolocates buildings with blocking calls
        study = await run_in_threadpool(parser.parse, files.file._file)
        return StudyDraftParseResult(study=study, errors=parser.errors)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/study-bundles", response_model=StudyBundlesResult)
async def get_study_bundles(
    q: str | None = Query(None, max_length=200),
    published: bool | None = Query(None),
    sort: BundleSort = Query("identifier"),
    desc: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.require_admin()),
) -> StudyBundlesResult:
    """Study drafts with their contribution, filtered by study identifier,
    name or contributors (`q`), paged and sorted (admin)."""
    return await StudyDraftService(session).find_bundles(
        q, published, sort, desc, skip, limit
    )


@router.get("/study-drafts", response_model=StudyDraftsResult)
async def get_study_drafts(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.require_admin()),
) -> StudyDraftsResult:
    """Get all study drafts"""
    service = StudyDraftService(session)
    studies = await service.list()
    return StudyDraftsResult(total=len(studies), skip=0, limit=None, data=studies)


@router.post("/study-draft", response_model=StudyDraft)
async def create_study_draft(
    study: StudyDraft = Body(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.get_user_info(required=False)),
) -> dict:
    """Create a study draft"""
    service = StudyDraftService(session)
    identifier = study.identifier
    if identifier and identifier != "_draft" and await service.exists(identifier):
        raise HTTPException(
            status_code=409,
            detail=f"Study with identifier {identifier} already exists.",
        )
    document = await service.createOrUpdate(study.model_dump(mode="json"))
    await ContributionService(session).touch_by_identifier(document["identifier"], user)
    return document


@router.get("/study-draft/{identifier}", response_model=StudyDraft)
async def get_study_draft(
    identifier: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get a study draft"""
    return await StudyDraftService(session).get(identifier)


@router.put("/study-draft/{identifier}", response_model=StudyDraft)
async def update_study_draft(
    identifier: str,
    study: StudyDraft = Body(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.get_user_info(required=False)),
) -> dict:
    """Update a study draft"""
    if identifier != study.identifier:
        raise HTTPException(
            status_code=400,
            detail="Identifier in URL does not match identifier in body",
        )
    document = await StudyDraftService(session).createOrUpdate(
        study.model_dump(mode="json")
    )
    await ContributionService(session).touch_by_identifier(document["identifier"], user)
    return document


@router.put("/study-draft/{identifier}/_publish", response_model=StudyRead)
async def publish_study_draft(
    identifier: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    engine: AsyncEngine = Depends(get_engine),
    user: User = Depends(kc_service.require_admin()),
) -> Study:
    """Save the study draft in the database, then load its measurements in
    the background (each dataset's `summary_status` reports the outcome).
    The version is bumped here for the catalog change and again by the
    background task once the aggregates hold the loaded measurements."""
    document = await StudyDraftService(session).get(identifier)
    try:
        study_draft = StudyDraft.model_validate(document)
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=e.errors(include_url=False, include_context=False),
        )
    study_service = StudyService(session)
    study = await study_service.save(study_draft)
    await ContributionService(session).publish_by_identifier(study.identifier, user)
    await CatalogVersionService(session).bump()
    await session.commit()
    background_tasks.add_task(load_published_study, engine, study.id)
    return study


@router.get("/dataset-loads", response_model=DatasetLoadsResult)
async def get_dataset_loads(
    status: Literal["pending", "ready", "failed"] | None = Query(None),
    study_id: int | None = Query(None),
    q: str | None = Query(None, max_length=200),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.require_admin()),
) -> DatasetLoadsResult:
    """Measurement load state of the published datasets (admin)."""
    return await DatasetService(session).find_loads(status, study_id, q, skip, limit)


@router.put("/study-draft/{identifier}/_reinstate", response_model=StudyRead)
async def reinstate_study_draft(
    identifier: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.require_admin()),
) -> Response:
    """Get the study from the database and push it in draft"""
    study_service = StudyService(session)
    results = await study_service.find(
        filter={"identifier": identifier}, sort=[], range=[]
    )
    if not results or results.total == 0:
        raise HTTPException(
            status_code=404, detail=f"Study with identifier {identifier} not found"
        )
    await StudyDraftService(session).reinstate(identifier)
    return Response(
        content="Study reinstated in draft",
        status_code=200,
        headers={
            "Location": f"{config.PATH_PREFIX}/contribute/study-draft/{identifier}"
        },
    )


@router.delete("/study-draft/{identifier}")
async def delete_study_draft(
    identifier: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.require_admin()),
) -> None:
    """Delete a study draft"""
    await StudyDraftService(session).delete(identifier)


@router.get("/contributions", response_model=ContributionsResult)
async def get_contributions(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> ContributionsResult:
    """Get all contributions"""
    service = ContributionService(session)
    res = await service.find(
        paramAsDict(filter), paramAsArray(sort), paramAsArray(range)
    )
    return res


@router.get("/contribution/{id}", response_model=Contribution)
async def get_contribution(
    session: AsyncSession = Depends(get_session),
    *,
    id: str,
) -> Contribution:
    """Get a contribution by id or study identifier"""
    service = ContributionService(session)
    if id.isdigit():
        res = await service.get(int(id))
    else:
        res = await service.get_by_identifier(id)
    return res


@router.delete("/contribution/{id}")
async def delete_contribution(
    id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.require_admin()),
) -> None:
    """Delete contribution by id or study identifier"""
    service = ContributionService(session)
    if id.isdigit():
        await service.delete(int(id))
    else:
        await service.delete_by_identifier(id)


@router.post(
    "/contribution/", response_model=Contribution, response_model_exclude_none=True
)
async def create_contribution(
    contribution: Contribution,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.get_user_info()),
) -> Contribution:
    """Create a contribution"""
    return await ContributionService(session).create(contribution, user)


@router.put(
    "/contribution/{id}", response_model=Contribution, response_model_exclude_none=True
)
async def update_contribution(
    id: str,
    contribution: Contribution,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.get_user_info(required=False)),
) -> Contribution:
    """Update a contribution by id"""
    return await ContributionService(session).update(id, contribution, user)
