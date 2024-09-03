"""
Handle / uploads
"""
import datetime

from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from api.services.s3 import s3_client

from fastapi import Depends, Security, Query, APIRouter, HTTPException
from fastapi.responses import Response

from api.utils.file_size import size_checker
from api.auth import get_api_key

from pydantic import BaseModel


class FilePath(BaseModel):
    paths: list[str]


router = APIRouter()


@router.get("/{file_path:path}",
            status_code=200,
            description="-- Download any assets from S3 --")
async def get_file(file_path: str,
                   download: bool = Query(
                       False, alias="d", description="Download file instead of inline display")):
    (body, content_type) = await s3_client.get_file(file_path)
    if body:
        if download:
            # download file
            return Response(content=body, media_type=content_type)
        else:
            # inline image
            return Response(content=body)
    else:
        raise HTTPException(status_code=404, detail="File not found")


@router.post("",
             status_code=200,
             description="-- Upload any assets to S3 --",
             dependencies=[Depends(size_checker)])
async def upload_files(
        files: list[UploadFile] = File(description="multiple file upload"), api_key: str = Security(get_api_key)):
    current_time = datetime.datetime.now()
    # generate unique name for the files' base folder in S3
    s3_folder = str(current_time.timestamp()).replace('.', '')
    return {"files": [await s3_client.upload_file(file, s3_folder=s3_folder) for file in files]}


@router.delete("",
               status_code=204,
               description="-- Delete asset present in S3 --",
               )
async def delete_files(filePath: FilePath, api_key: str = Security(get_api_key)):
    [await s3_client.delete_file(path) for path in filePath.paths]
    return
