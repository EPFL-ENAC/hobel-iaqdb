import pkg_resources
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from api.config import config
from api.db import get_session, AsyncSession
from api.services.study_parser import StudyParser
from api.services.study import StudyService
from api.services.study_draft import StudyDraftService
from api.services.contribution import ContributionService
from api.models.catalog import StudyDraft, StudyDraftsResult, StudyBundlesResult, StudyBundle, StudyRead, Study, Contribution, ContributionsResult
from api.utils.files import file_checker
from api.auth import kc_service, User
from enacit4r_sql.utils.query import paramAsArray, paramAsDict
from datetime import datetime

router = APIRouter()


@router.get("/study-template")
async def get_study_template():
    version = "3.2.1"
    data_file_path = pkg_resources.resource_filename(
        "api", f"data/Metadata_entry_form_v{version}.xlsm")
    return FileResponse(data_file_path, filename=f"iaqdb_study_template_v{version}.xlsm", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/dataset-dictionary")
async def get_dataset_dictionary():
    data_file_path = pkg_resources.resource_filename(
        "api", "data/Dictionary_data.xlsx")
    return FileResponse(data_file_path, filename="iaqdb_dataset_dictionary.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/study-excel",
             status_code=200,
             dependencies=[Depends(file_checker.check_size)],
             response_model=StudyDraft)
async def read_study_from_excel(
    files: UploadFile = File(
        description="Excel file containing study, building, space descriptions")):
    try:
        study = StudyParser().parse(files.file._file)
        return study
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/study-bundles", response_model=StudyBundlesResult)
async def get_study_bundles(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.require_admin()),
) -> StudyBundlesResult:
    """Get all study bundles"""
    service = StudyDraftService()
    studies = await service.list()
    if not studies:
        return StudyBundlesResult(total=0, skip=0, limit=None, data=[])
    # Convert StudyDraft to StudyBundle
    contribService = ContributionService(session)
    bundles = []
    contributions = await contribService.find(
        filter={'study_identifier': [study.identifier for study in studies]},
        sort=[],
        range=[]
    )
    contributions_map = {
        contribution.study_identifier: contribution for contribution in contributions.data}
    for study in studies:
        bundle = StudyBundle(
            study=study,
            contribution=contributions_map.get(study.identifier, None)
        )
        bundles.append(bundle)
    return StudyBundlesResult(total=len(studies), skip=0, limit=None, data=bundles)


@router.get("/study-drafts", response_model=StudyDraftsResult)
async def get_study_drafts(
    user: User = Depends(kc_service.require_admin()),
) -> StudyDraftsResult:
    """Get all study drafts"""
    service = StudyDraftService()
    studies = await service.list()
    return StudyDraftsResult(total=len(studies), skip=0, limit=None, data=studies)


@router.post("/study-draft", response_model=StudyDraft)
async def create_study_draft(
    study: StudyDraft = Body(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.get_user_info(required=False)),
) -> StudyDraft:
    """Create a study draft"""
    service = StudyDraftService()
    if study.identifier is not None and study.identifier != "" and study.identifier != "_draft":
        exists = await service.exists(study.identifier)
        if exists:
            raise Exception(
                f"Study with identifier {study.identifier} already exists.")
    study = await service.createOrUpdate(StudyDraft.model_validate(study))
    await ContributionService(session).touch_by_identifier(study.identifier, user)
    return study


@router.get("/study-draft/{identifier}", response_model=StudyDraft)
async def get_study_draft(
    identifier: str,
) -> StudyDraft:
    """Get a study draft"""
    service = StudyDraftService()
    try:
        study = await service.get(identifier)
        return study
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/study-draft/{identifier}", response_model=StudyDraft)
async def update_study_draft(
    identifier: str,
    study: StudyDraft = Body(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.get_user_info(required=False)),
) -> StudyDraft:
    """Update a study draft"""
    if identifier != study.identifier:
        raise Exception("Identifier in URL does not match identifier in body")
    service = StudyDraftService()
    study = await service.createOrUpdate(StudyDraft.model_validate(study))
    await ContributionService(session).touch_by_identifier(study.identifier, user)
    return study


@router.put("/study-draft/{identifier}/_publish", response_model=StudyRead)
async def publish_study_draft(
    identifier: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.require_admin()),
) -> Study:
    """Save the study draft in the database"""
    service = StudyDraftService()
    study_draft = await service.get(identifier)
    study_service = StudyService(session)
    study = await study_service.save(study_draft)
    await ContributionService(session).publish_by_identifier(study.identifier, user)
    return study


@router.put("/study-draft/{identifier}/_reinstate", response_model=StudyRead)
async def reinstate_study_draft(
    identifier: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.require_admin()),
) -> Response:
    """Get the study from the database and push it in draft"""
    study_service = StudyService(session)
    results = await study_service.find(filter={'identifier': identifier}, sort=[], range=[])
    if not results or results.total == 0:
        raise HTTPException(
            status_code=404, detail=f"Study with identifier {identifier} not found")
    service = StudyDraftService()
    await service.reinstate(identifier)
    return Response(
        content="Study reinstated in draft",
        status_code=200,
        headers={
            "Location": f"{config.PATH_PREFIX}/contribute/study-draft/{identifier}"}
    )


@router.delete("/study-draft/{identifier}")
async def delete_study_draft(
    identifier: str,
    user: User = Depends(kc_service.require_admin()),
) -> None:
    """Delete a study draft"""
    service = StudyDraftService()
    await service.delete(identifier)


@router.get("/contributions", response_model=ContributionsResult)
async def get_contributions(
    filter: str = Query(None),
    sort: str = Query(None),
    range: str = Query(None),
    session: AsyncSession = Depends(get_session),
) -> ContributionsResult:
    """Get all contributions"""
    service = ContributionService(session)
    res = await service.find(paramAsDict(filter), paramAsArray(sort), paramAsArray(range))
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


@router.post("/contribution/", response_model=Contribution, response_model_exclude_none=True)
async def create_contribution(
    contribution: Contribution,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.get_user_info())
) -> Contribution:
    """Create a contribution"""
    return await ContributionService(session).create(contribution, user)


@router.put("/contribution/{id}", response_model=Contribution, response_model_exclude_none=True)
async def update_contribution(
    id: str,
    contribution: Contribution,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.get_user_info(required=False))
) -> Contribution:
    """Update a contribution by id"""
    return await ContributionService(session).update(id, contribution, user)
