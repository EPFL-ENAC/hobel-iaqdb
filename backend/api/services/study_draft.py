import os
import uuid
import json
import tempfile
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
                            new_path = await s3_client.move_file(file["path"], dataset_file_path)
                            file["path"] = new_path
                            dataset.folder["children"][i] = file
                dataset.folder["name"] = dataset.name
                dataset.folder["path"] = f"{config.S3_PATH_PREFIX}{s3_folder}/files/{dataset.name}"

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
