"""Make the study files under S3_PATH_PREFIX private. Uploads and copies used to
be `public-read`, which let anyone who knew a URL read drafts and embargoed
data directly from S3. One-off, safe to re-run."""

import argparse
import asyncio

from api.config import config
from api.services.s3 import COPY_CONCURRENCY, s3_client

# the app's own folders: anything else under the prefix may be public on purpose
FOLDERS = ("tmp", "draft", "pub", "downloads")


async def run(apply: bool) -> int:
    """Returns the number of objects whose ACL could not be changed."""
    keys = []
    for folder in FOLDERS:
        found = await s3_client.list_files(f"{folder}/")
        print(f"{len(found)} objects under {config.S3_PATH_PREFIX}{folder}/")
        keys += found
    failures = []
    semaphore = asyncio.Semaphore(COPY_CONCURRENCY)

    async def make_private(key: str) -> None:
        async with semaphore, s3_client._client() as client:
            try:
                await client.put_object_acl(
                    Bucket=s3_client.bucket, Key=key, ACL="private"
                )
            except Exception as e:
                failures.append(key)
                print(f"FAILED {key}: {type(e).__name__}: {e}")

    if apply:
        await asyncio.gather(*(make_private(key) for key in keys))
        print(f"{len(keys) - len(failures)} made private, {len(failures)} failed")
    await s3_client.close()
    return len(failures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="default: only count")
    raise SystemExit(1 if asyncio.run(run(parser.parse_args().apply)) else 0)
