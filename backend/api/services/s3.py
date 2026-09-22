import asyncio
from pathlib import Path

from api.config import config
from enacit4r_files.services.s3 import S3Service

s3_client = S3Service(
    config.S3_ENDPOINT_PROTOCOL + config.S3_ENDPOINT_HOSTNAME,
    config.S3_ACCESS_KEY_ID,
    config.S3_SECRET_ACCESS_KEY,
    config.S3_REGION,
    config.S3_BUCKET,
    config.S3_PATH_PREFIX,
)

# CopyObject refuses objects above 5 GB, those are copied in parts instead
COPY_OBJECT_MAX_SIZE = 5 << 30
COPY_PART_SIZE = 512 << 20
# In-flight copies; bounded by the connection pool of the shared client
COPY_CONCURRENCY = 8


async def copy_object(source_key: str, destination_key: str) -> None:
    """Server-side copy of one object, given full S3 keys, whatever its size."""
    async with s3_client._client() as client:
        head = await client.head_object(Bucket=s3_client.bucket, Key=source_key)
        if head["ContentLength"] <= COPY_OBJECT_MAX_SIZE:
            await client.copy_object(
                Bucket=s3_client.bucket,
                CopySource={"Bucket": s3_client.bucket, "Key": source_key},
                Key=destination_key,
                ACL="public-read",
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
        ACL="public-read",
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
