import json
import urllib.parse
import uuid

from api.db import AsyncSession
from api.models.catalog import StudyDraftDocument
from api.services.s3 import copy_objects, delete_objects, s3_client
from api.services.study_file import StudyFileService
from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import select


def check_identifier(identifier: str) -> None:
    """The identifier is part of the S3 keys of the study."""
    if not isinstance(identifier, str) or "/" in identifier or ".." in identifier:
        raise HTTPException(status_code=400, detail="Invalid study identifier")


def referenced_keys(identifier: str, document: dict) -> set[str]:
    """S3 keys of the draft folder that the document's datasets refer to."""
    folder = s3_client.to_s3_key(f"draft/{identifier}/")
    keys = {
        s3_client.to_s3_key(file.get("path") or "")
        for dataset in document.get("datasets") or []
        for file in (dataset.get("folder") or {}).get("children") or []
    }
    return {key for key in keys if key.startswith(folder)}


class StudyDraftService:
    """Study drafts are raw JSON documents in the database, validated only on
    publish; their files are in S3, indexed by StudyFileService."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.files = StudyFileService(session)

    async def createOrUpdate(self, document: dict) -> dict:
        identifier = document.get("identifier")
        if not identifier or identifier == "_draft":
            identifier = str(uuid.uuid4())
            document["identifier"] = identifier
        check_identifier(identifier)

        # Destination folder in s3
        s3_folder = f"draft/{identifier}"

        # Move tmp files to their final location
        for dataset in document.get("datasets") or []:
            folder = dataset.get("folder")
            if not folder:
                continue
            for file in folder.get("children") or []:
                if "/tmp/" in file["path"]:
                    dataset_file_path = (
                        f"{s3_folder}/files/{dataset['name']}/{file['name']}"
                    )
                    new_key = await s3_client.move_file(file["path"], dataset_file_path)
                    file["path"] = urllib.parse.quote(new_key)
            folder["name"] = dataset["name"]
            folder["path"] = s3_client.to_s3_path(
                urllib.parse.quote(f"{s3_folder}/files/{dataset['name']}")
            )

        # TODO Remove files that are not linked to a dataset

        statement = insert(StudyDraftDocument).values(
            identifier=identifier, document=document
        )
        await self.session.exec(
            statement.on_conflict_do_update(
                index_elements=[StudyDraftDocument.identifier],
                set_={"document": statement.excluded.document},
            )
        )
        await self.files.add(identifier, "draft", referenced_keys(identifier, document))
        await self.session.commit()
        return document

    async def delete(self, identifier: str) -> None:
        draft = await self.session.get(StudyDraftDocument, identifier)
        if not draft:
            raise HTTPException(
                status_code=404, detail=f"Study draft {identifier} does not exist."
            )
        keys = await self.files.remove(identifier, "draft")
        await self.session.delete(draft)
        await self.session.commit()
        await delete_objects(keys)

    async def exists(self, identifier: str) -> bool:
        return await self.session.get(StudyDraftDocument, identifier) is not None

    async def get(self, identifier: str) -> dict:
        draft = await self.session.get(StudyDraftDocument, identifier)
        if not draft:
            raise HTTPException(
                status_code=404, detail=f"Study draft {identifier} does not exist."
            )
        return draft.document

    async def list(self) -> list[dict]:
        """List all study drafts"""
        res = await self.session.exec(
            select(StudyDraftDocument.document).order_by(StudyDraftDocument.identifier)
        )
        return list(res.all())

    async def reinstate(self, identifier: str) -> None:
        """Replace the study draft by the published study and its files."""
        content, _ = await s3_client.get_file(f"pub/{identifier}/study.json")
        if not content:
            raise HTTPException(
                status_code=404, detail=f"Published study {identifier} not found."
            )
        document = json.loads(content)

        if await self.exists(identifier):
            await self.delete(identifier)

        pairs = [
            (key, key.replace("/pub/", "/draft/"))
            for key in await self.files.keys(identifier, "pub")
        ]
        await copy_objects(pairs)
        await self.files.add(identifier, "draft", [draft for _, draft in pairs])

        for dataset in document.get("datasets") or []:
            folder = dataset.get("folder")
            if not folder:
                continue
            folder["path"] = folder["path"].replace("/pub/", "/draft/")
            for file in folder.get("children") or []:
                file["path"] = file["path"].replace("/pub/", "/draft/")
        await self.createOrUpdate(document)
