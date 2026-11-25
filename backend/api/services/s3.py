import asyncio
import re
from pathlib import Path
from typing import AsyncIterator

from api.config import config
from botocore.exceptions import ClientError
from enacit4r_files.services.s3 import S3Service

s3_client = S3Service(
    config.S3_ENDPOINT_PROTOCOL + config.S3_ENDPOINT_HOSTNAME,
    config.S3_ACCESS_KEY_ID,
    config.S3_SECRET_ACCESS_KEY,
    config.S3_REGION,
    config.S3_BUCKET,
    config.S3_PATH_PREFIX,
    acl=None,  # private: objects are only served through the API
)

# CopyObject refuses objects above 5 GB, those are copied in parts instead
COPY_OBJECT_MAX_SIZE = 5 << 30
COPY_PART_SIZE = 512 << 20
# In-flight copies; bounded by the connection pool of the shared client
COPY_CONCURRENCY = 8


def tmp_key(path: str) -> str | None:
    """Full S3 key of an upload not saved in a study draft yet, None for any
    other path: anonymous clients choose it, and may delete or move that key."""
    key = s3_client.to_s3_key(path)
    if not key.startswith(f"{s3_client.path_prefix}tmp/") or ".." in key.split("/"):
        return None
    return key


def is_secret_tmp_key(key: str) -> bool:
    """Whether the upload is in an unguessable folder, only known by the client
    that uploaded it (folders used to be named after the time)."""
    folder = key.removeprefix(f"{s3_client.path_prefix}tmp/").split("/")[0]
    return re.fullmatch("[0-9a-f]{32}", folder) is not None


async def copy_object(source_key: str, destination_key: str) -> None:
    """Server-side copy of one object, given full S3 keys, whatever its size.
    The copy is private: objects are only served through the API."""
    async with s3_client._client() as client:
        head = await client.head_object(Bucket=s3_client.bucket, Key=source_key)
        if head["ContentLength"] <= COPY_OBJECT_MAX_SIZE:
            await client.copy_object(
                Bucket=s3_client.bucket,
                CopySource={"Bucket": s3_client.bucket, "Key": source_key},
                Key=destination_key,
            )
            return
        await _copy_object_in_parts(client, source_key, destination_key, head)


async def _copy_object_in_parts(
    client, source_key: str, destination_key: str, head: dict
) -> None:
    bucket = s3_client.bucket
    upload = await client.create_multipart_upload(
        Bucket=bucket,
        Key=destination_key,
        ContentType=head["ContentType"],
    )
    upload_id = upload["UploadId"]
    try:
        parts = []
        size = head["ContentLength"]
        for number, start in enumerate(range(0, size, COPY_PART_SIZE), start=1):
            end = min(start + COPY_PART_SIZE, size) - 1
            part = await client.upload_part_copy(
                Bucket=bucket,
                Key=destination_key,
                UploadId=upload_id,
                PartNumber=number,
                CopySource={"Bucket": bucket, "Key": source_key},
                CopySourceRange=f"bytes={start}-{end}",
            )
            parts.append({"PartNumber": number, "ETag": part["CopyPartResult"]["ETag"]})
        await client.complete_multipart_upload(
            Bucket=bucket,
            Key=destination_key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
    except BaseException:
        await client.abort_multipart_upload(
            Bucket=bucket, Key=destination_key, UploadId=upload_id
        )
        raise


async def copy_objects(pairs: list[tuple[str, str]]) -> None:
    """Copy (source_key, destination_key) pairs concurrently."""
    semaphore = asyncio.Semaphore(COPY_CONCURRENCY)

    async def copy_one(source_key: str, destination_key: str) -> None:
        async with semaphore:
            await copy_object(source_key, destination_key)

    await asyncio.gather(*(copy_one(*pair) for pair in pairs))


async def download_object(key: str, path: Path) -> Path:
    """Stream one object, given its full S3 key, to a local file."""
    async with s3_client._client() as client:
        response = await client.get_object(Bucket=s3_client.bucket, Key=key)
        with path.open("wb") as stream:
            async for chunk in response["Body"].iter_chunks(1 << 20):
                stream.write(chunk)
    return path


async def head_object(key: str) -> dict | None:
    """Metadata of one object, given its full S3 key, None if it does not exist."""
    async with s3_client._client() as client:
        try:
            return await client.head_object(Bucket=s3_client.bucket, Key=key)
        except ClientError as e:
            if e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return None
            raise


async def stream_object(key: str) -> AsyncIterator[bytes]:
    """Content of one object, given its full S3 key, never held in memory."""
    async with s3_client._client() as client:
        response = await client.get_object(Bucket=s3_client.bucket, Key=key)
        body = response["Body"]
        # not `as body`: entering it returns the raw aiohttp response
        async with body:
            async for chunk in body.iter_chunks(1 << 20):
                yield chunk


async def delete_objects(keys: list[str]) -> None:
    """Delete objects, given full S3 keys, concurrently."""
    semaphore = asyncio.Semaphore(COPY_CONCURRENCY)

    async def delete_one(key: str) -> None:
        async with semaphore, s3_client._client() as client:
            await client.delete_object(Bucket=s3_client.bucket, Key=key)

    await asyncio.gather(*(delete_one(key) for key in keys))
