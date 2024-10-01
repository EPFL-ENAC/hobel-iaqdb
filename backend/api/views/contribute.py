from typing import List
from fastapi import APIRouter, Security, Depends, Query, Body
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from api.db import get_session, AsyncSession
from api.auth import get_api_key
from api.services.study import StudyService
from api.services.study_parser import StudyParser
from api.services.study_draft import StudyDraftService
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


@router.post("/study-draft", response_model=StudyDraft)
async def create_study_draft(
    study: StudyDraft = Body(...),
) -> StudyDraft:
    """Create a study draft"""
    service = StudyDraftService()
    if study.identifier is not None and study.identifier != "" and study.identifier != "_draft":
        exists = await service.exists(study.identifier)
        if exists:
            raise Exception(
                f"Study with identifier {study.identifier} already exists.")
    study = await service.createOrUpdate(StudyDraft.model_validate(study))
    return study


@router.get("/study-draft/{identifier}", response_model=StudyDraft)
async def get_study_draft(
    identifier: str,
) -> StudyDraft:
    """Get a study draft"""
    service = StudyDraftService()
    study = await service.get(identifier)
    return study


@router.put("/study-draft/{identifier}", response_model=StudyDraft)
async def update_study_draft(
    identifier: str,
    study: StudyDraft = Body(...),
) -> StudyDraft:
    """Update a study draft"""
    if identifier != study.identifier:
        raise Exception("Identifier in URL does not match identifier in body")
    service = StudyDraftService()
    study = await service.createOrUpdate(StudyDraft.model_validate(study))
    return study
