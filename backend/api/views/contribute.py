import pkg_resources
from typing import List
from fastapi import APIRouter, Depends, Body, HTTPException
from fastapi.responses import FileResponse
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from api.services.study_parser import StudyParser
from api.services.study_draft import StudyDraftService
from api.models.catalog import StudyDraft, StudyDraftsResult
from api.utils.files import file_checker
from api.auth import require_admin, User

router = APIRouter()


@router.get("/study-template")
async def get_study_template():
    version = "2.1"
    data_file_path = pkg_resources.resource_filename(
        "api", f"data/Metadata_entry_form_v{version}.xlsm")
    return FileResponse(data_file_path, filename=f"iaqdb_study_template_v{version}.xlsm", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/dataset-dictionary")
async def get_study_template():
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


@router.get("/study-drafts", response_model=StudyDraftsResult)
async def get_study_drafts(
    user: User = Depends(require_admin),
) -> StudyDraftsResult:
    """Get all study drafts"""
    service = StudyDraftService()
    studies = await service.list()
    return StudyDraftsResult(total=len(studies), skip=0, limit=None, data=studies)


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
    try:
        study = await service.get(identifier)
        return study
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


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


@router.delete("/study-draft/{identifier}")
async def delete_study_draft(
    identifier: str,
) -> None:
    """Delete a study draft"""
    service = StudyDraftService()
    await service.delete(identifier)
