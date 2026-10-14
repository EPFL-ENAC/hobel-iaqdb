"""Read the study drafts and files that the former draft storage left in S3,
for the migration that moves drafts to the database and indexes the files."""

import asyncio
import json

from api.services.s3 import COPY_CONCURRENCY, s3_client


async def read_s3() -> tuple[list[dict], list[dict]]:
    """Rows of the study_draft and study_file tables."""
    semaphore = asyncio.Semaphore(COPY_CONCURRENCY)

    async def read_draft(identifier: str, key: str) -> dict:
        async with semaphore:
            content, _ = await s3_client.get_file(key)
        document = json.loads(content)
        document["identifier"] = identifier
        return {"identifier": identifier, "document": document}

    jobs, files = [], []
    for area in ("draft", "pub"):
        root = s3_client.to_s3_key(f"{area}/")
        for key in await s3_client.list_files(f"{area}/"):
            identifier, _, name = key[len(root) :].partition("/")
            if not identifier or not name:
                continue
            if name != "study.json":
                files.append({"key": key, "study_identifier": identifier, "area": area})
            elif area == "draft":
                jobs.append(read_draft(identifier, key))
    drafts = await asyncio.gather(*jobs)
    await s3_client.close()
    return drafts, files
