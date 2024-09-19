import os
import uuid
import json
import tempfile
from api.services.s3 import s3_client
from api.models.catalog import Study, Dataset


class StudyDraftService:

    async def createOrUpdate(self, study: Study) -> Study:
        if study.identifier is None or study.identifier == "" or study.identifier == "_draft":
            study.identifier = str(uuid.uuid4())
        else:
            exists = await self.exists(study.identifier)
            if not exists:
                raise Exception(
                    f"Study with identifier {study.identifier} does not exist.")

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Temporary directory created at: {temp_dir}")

            # Use the temporary directory for file operations
            temp_file_path = os.path.join(temp_dir, "study.json")

            # Convert SQLModel object to dictionary
            study_dict = study.model_dump()
            with open(temp_file_path, "w") as temp_file:
                json.dump(study_dict, temp_file, indent=2)

            s3_folder = f"draft/{study.identifier}"

            await s3_client.upload_local_file(temp_dir, "study.json", s3_folder=s3_folder)
        return study

    async def exists(self, identifier: str) -> bool:
        return await s3_client.path_exists(f"draft/{identifier}/study.json")

    async def get(self, identifier: str) -> Study:
        exists = await self.exists(identifier)
        if not exists:
            raise Exception(
                f"Study with identifier {identifier} does not exist.")

        file_path = f"draft/{identifier}/study.json"
        content, mime_type = await s3_client.get_file(file_path)
        study_dict = json.load(content)
        return Study(**study_dict)
