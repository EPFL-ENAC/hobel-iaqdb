"""
Handle / uploads
"""
import uuid
from urllib.parse import quote

from api.auth import User, is_admin, kc_service
from api.db import AsyncSession, get_session
from api.services.s3 import (
    delete_objects,
    head_object,
    is_secret_tmp_key,
    s3_client,
    stream_object,
    tmp_key,
)
from api.services.study_file import StudyFileService
from api.utils.files import file_checker
from fastapi import APIRouter, Depends, HTTPException
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


class FilePath(BaseModel):
    paths: list[str]


router = APIRouter()


@router.get(
    "/{file_path:path}",
    status_code=200,
    description="-- Download any assets from S3 (admin), or own uploads --",
)
async def get_file(
    file_path: str,
    session: AsyncSession = Depends(get_session),
    user: User | None = Depends(kc_service.get_user_info(required=False)),
):
    """Admins read any file: they include studies under data embargo and the
    archives of the download links. Contributors, who are anonymous, read their
    uploads and the files of their draft until it is published. Contributors
    upload any content, so it is never displayed inline."""
    if not is_admin(user):
        upload = tmp_key(file_path)
        if not (
            is_secret_tmp_key(upload)
            if upload
            else await StudyFileService(session).is_open_draft(
                s3_client.to_s3_key(file_path)
            )
        ):
            raise HTTPException(
                status_code=403, detail="You are not authorised to read this file"
            )
    key = s3_client.to_s3_key(file_path)
    head = await head_object(key)
    if head is None:
        raise HTTPException(status_code=404, detail="File not found")
    return StreamingResponse(
        stream_object(key),
        media_type=head["ContentType"],
        headers={
            "Content-Disposition": "attachment;"
            f" filename*=UTF-8''{quote(key.split('/')[-1])}",
            "Content-Length": str(head["ContentLength"]),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post(
    "/tmp",
    status_code=200,
    description="-- Upload any assets to S3 --",
    dependencies=[Depends(file_checker.check_size)],
)
async def upload_temp_files(
    files: list[UploadFile] = File(description="multiple file upload"),
):
    # unguessable name for the files' base folder in S3: knowing it gives access
    folder_name = uuid.uuid4().hex
    folder_path = f"tmp/{folder_name}"
    children = [
        await s3_client.upload_file(file, s3_folder=folder_path) for file in files
    ]
    parent_path = s3_client.to_s3_path(folder_path)
    return {
        "name": folder_name,
        "path": parent_path,
        "is_file": False,
        "children": children,
    }


@router.delete(
    "/{file_path:path}",
    status_code=204,
    description="-- Delete temporary asset present in S3 --",
)
async def delete_temp_files(file_path: str):
    # anything but an upload not saved yet is left to the study draft routes
    key = tmp_key(file_path)
    if key:
        await delete_objects([key])
    return
