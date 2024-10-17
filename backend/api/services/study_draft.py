import os
import uuid
import json
import tempfile
import urllib.parse
from api.services.s3 import s3_client
from api.config import config
from api.models.catalog import Study, StudyDraft


class StudyDraftService:

    async def createOrUpdate(self, study: Study) -> Study:
        if study.identifier is None or study.identifier == "" or study.identifier == "_draft":
            study.identifier = str(uuid.uuid4())

        # Destination folder in s3
        s3_folder = f"draft/{study.identifier}"

        # Move tmp files to their final location
        if study.datasets is not None:
            for dataset in study.datasets:
                if "children" in dataset.folder:
                    for i, file in enumerate(dataset.folder["children"]):
                        if "/tmp/" in file["path"]:
                            dataset_file_path = f"{s3_folder}/files/{dataset.name}/{file['name']}"
                            new_key = await s3_client.move_file(file["path"], dataset_file_path)
                            file["path"] = urllib.parse.quote(new_key)
                            dataset.folder["children"][i] = file
                dataset.folder["name"] = dataset.name
                dataset.folder["path"] = s3_client.to_s3_path(
                    urllib.parse.quote(f"{s3_folder}/files/{dataset.name}"))

        # TODO Remove files that are not linked to a dataset

        # Create a temporary directory to dump JSON
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Temporary directory created at: {temp_dir}")

            # Use the temporary directory for file operations
            temp_file_path = os.path.join(temp_dir, "study.json")

            # Convert SQLModel object to dictionary
            study_dict = study.model_dump()
            with open(temp_file_path, "w") as temp_file:
                json.dump(study_dict, temp_file, indent=2)
            await s3_client.upload_local_file(temp_dir, "study.json", s3_folder=s3_folder)

        return study

    async def delete(self, identifier: str):
        exists = await self.exists(identifier)
        if not exists:
            raise Exception(
                f"Study with identifier {identifier} does not exist.")

        await s3_client.delete_files(f"draft/{identifier}")

    async def exists(self, identifier: str) -> bool:
        return await s3_client.path_exists(f"draft/{identifier}/study.json")

    async def get(self, identifier: str) -> StudyDraft:
        exists = await self.exists(identifier)
        if not exists:
            raise Exception(
                f"Study with identifier {identifier} does not exist.")

        file_path = f"draft/{identifier}/study.json"
        content, mime_type = await s3_client.get_file(file_path)
        study_dict = json.loads(content)
        return StudyDraft(**study_dict)

    async def list(self) -> list[StudyDraft]:
        """List all studies"""
        folder_path = "draft/"
        files = [study_file for study_file in await s3_client.list_files(folder_path) if study_file.endswith("/study.json")]

        study_drafts = []
        for file in files:
            content, mime_type = await s3_client.get_file(file)
            study_dict = json.loads(content)
            study_drafts.append(StudyDraft(**study_dict))

        return study_drafts
