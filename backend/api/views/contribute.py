import pkg_resources
from typing import List
from fastapi import APIRouter, Depends, Body
from fastapi.responses import FileResponse
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from api.services.study_parser import StudyParser
from api.services.study_draft import StudyDraftService
from api.models.catalog import StudyDraft
from api.utils.file_size import size_checker

router = APIRouter()


@router.get("/study-template")
async def get_study_template():
    data_file_path = pkg_resources.resource_filename(
        "api", "data/Metadata_entry_form.xlsx")
    return FileResponse(data_file_path, filename="iaqdb_study_template.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/dataset-dictionary")
async def get_study_template():
    data_file_path = pkg_resources.resource_filename(
        "api", "data/Dictionary_data.xlsx")
    return FileResponse(data_file_path, filename="iaqdb_dataset_dictionary.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


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
