"""Bulk-import studies from SEED_DATA, following the Contribute flow:
upload files to tmp -> create study draft -> publish.

Expected layout, one folder per study named by its identifier:

    SEED_DATA/<identifier>/metadata.json          study draft (source of truth)
    SEED_DATA/<identifier>/<type>/**/*.csv|*.zip  processed data files

where <type> is e.g. time_series, time_integrated, statistical or
source_packages. Files are matched to the datasets of metadata.json through
the `source_outer_file` column of the processed CSV (also inside zips), which
names the file originally uploaded for that dataset. Datasets that no file
refers to are dropped from the import with a warning.

Files are uploaded straight to the study draft on S3, in concurrent parts. A
re-run only uploads what changed: the MD5 of each file is stored with the S3
object and cached locally (SEED_DATA/.seed-cache.json, keyed by size and
mtime) so unchanged files are neither read nor uploaded again.

Usage:
    python -m api.scripts.seed                    import all studies
    python -m api.scripts.seed <identifier>...    import only these studies
    python -m api.scripts.seed --check            validate only, write nothing
"""

import argparse
import asyncio
import csv
import hashlib
import io
import json
import re
import sys
import time
import traceback
import urllib.parse
import zipfile
from dataclasses import dataclass
from pathlib import Path

from api.config import config
from api.models.catalog import DatasetDraft, StudyDraft
from api.services.s3 import s3_client
from api.services.study import StudyService
from api.services.study_draft import StudyDraftService
from botocore.exceptions import ClientError
from enacit4r_files.models.files import FileRef
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

SEED_DATA = Path(__file__).resolve().parents[2] / "SEED_DATA"
MD5_CACHE = SEED_DATA / ".seed-cache.json"
# Object metadata key holding the MD5 of the uploaded content
MD5_METADATA = "seed-md5"
# Files bigger than one part are uploaded in concurrent parts (min 5 MiB)
PART_SIZE = 32 << 20
# In-flight parts, all files together: bounds memory to CONCURRENCY x PART_SIZE
# and stays within the connection pool of the shared S3 client
UPLOAD_CONCURRENCY = 8


@dataclass
class SeedStudy:
    folder: Path
    draft: StudyDraft
    dataset_files: list[tuple[DatasetDraft, list[Path]]]
    warnings: list[str]


def visible_entries(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if not p.name.startswith("."))


def data_files(folder: Path) -> list[Path]:
    """Every file below the study folder, except the ones at its root."""
    return sorted(
        p
        for p in folder.rglob("*")
        if p.is_file()
        and p.parent != folder
        and not any(part.startswith(".") for part in p.relative_to(folder).parts)
    )


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()


def first_source_file(stream) -> str | None:
    """Read `source_outer_file` from the first data row of a processed CSV,
    None if the CSV has a header but no row."""
    reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"))
    if reader.fieldnames is None or "source_outer_file" not in reader.fieldnames:
        raise ValueError("no `source_outer_file` column")
    row = next(reader, None)
    return None if row is None else row["source_outer_file"]


def source_files(path: Path) -> set[str]:
    """Names of the originally uploaded files a processed file was built from."""
    names = set()
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if member.endswith(".csv"):
                    with archive.open(member) as stream:
                        names.add(first_source_file(stream))
    else:
        with path.open("rb") as stream:
            names.add(first_source_file(stream))
    names.discard(None)  # header-only csv
    if not names:
        raise ValueError(f"{path.name} contains no data row")
    return names


def match_files_to_datasets(
    folder: Path, draft: StudyDraft, files: list[Path]
) -> tuple[list[tuple[DatasetDraft, list[Path]]], list[str]]:
    """Assign each processed file to exactly one dataset of the draft."""
    datasets_by_source: dict[str, list[DatasetDraft]] = {}
    for dataset in draft.datasets:
        for child in (dataset.folder or {}).get("children") or []:
            datasets_by_source.setdefault(normalize_name(child["name"]), []).append(
                dataset
            )

    files_by_dataset: dict[int, list[Path]] = {}
    for path in files:
        sources = source_files(path)
        candidates = {
            id(d): d
            for name in sources
            for d in datasets_by_source.get(normalize_name(name), [])
        }
        if len(candidates) != 1:
            raise ValueError(
                f"{path.relative_to(folder)} built from {sorted(sources)} "
                f"matches {len(candidates)} dataset(s) "
                f"{sorted(d.name for d in candidates.values())}, expected 1"
            )
        files_by_dataset.setdefault(candidates.popitem()[0], []).append(path)

    matched, warnings = [], []
    for dataset in draft.datasets:
        paths = files_by_dataset.get(id(dataset))
        if paths:
            matched.append((dataset, paths))
        else:
            warnings.append(f"dataset '{dataset.name}' has no file, dropped")
    if not matched:
        raise ValueError("no dataset has a file")
    return matched, warnings


def load_study(folder: Path) -> SeedStudy:
    """Read and validate one study folder, without touching DB or S3."""
    draft = StudyDraft.model_validate_json((folder / "metadata.json").read_text())
    if draft.identifier != folder.name:
        raise ValueError(
            f"folder name does not match metadata identifier '{draft.identifier}'"
        )

    files = data_files(folder)
    if not files:
        raise ValueError("no data file")
    dataset_files, warnings = match_files_to_datasets(folder, draft, files)
    return SeedStudy(
        folder=folder, draft=draft, dataset_files=dataset_files, warnings=warnings
    )


def draft_file_key(identifier: str, dataset: DatasetDraft, path: Path) -> str:
    """S3 key of a dataset file in the study draft, where the Contribute flow
    moves uploaded files."""
    return s3_client.to_s3_key(f"draft/{identifier}/files/{dataset.name}/{path.name}")


class Md5Cache:
    """MD5 of local files, invalidated by size and mtime, so a re-run does not
    read SEED_DATA again."""

    def __init__(self, file: Path):
        self.file = file
        self.entries: dict[str, dict] = (
            json.loads(file.read_text()) if file.exists() else {}
        )

    def get(self, path: Path) -> str:
        stat = path.stat()
        entry = self.entries.get(str(path))
        if entry and (entry["size"], entry["mtime_ns"]) == (
            stat.st_size,
            stat.st_mtime_ns,
        ):
            return entry["md5"]
        md5 = md5_of(path)
        self.entries[str(path)] = {
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "md5": md5,
        }
        return md5

    def save(self) -> None:
        self.file.write_text(json.dumps(self.entries, indent=1))


def md5_of(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_part(path: Path, start: int) -> bytes:
    with path.open("rb") as stream:
        stream.seek(start)
        return stream.read(PART_SIZE)


async def head_object(key: str) -> dict | None:
    """S3 object metadata, None if the object does not exist."""
    async with s3_client._client() as client:
        try:
            return await client.head_object(Bucket=s3_client.bucket, Key=key)
        except ClientError as e:
            if e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return None
            raise


async def is_uploaded(key: str, path: Path, md5: str) -> bool:
    """Whether the draft file in S3 already holds the content of `path`."""
    head = await head_object(key)
    return (
        head is not None
        and head["ContentLength"] == path.stat().st_size
        and head["Metadata"].get(MD5_METADATA) == md5
    )


async def upload_parts(
    client, key: str, path: Path, upload_id: str, semaphore: asyncio.Semaphore
) -> list[dict]:
    async def upload_part(number: int, start: int) -> dict:
        async with semaphore:
            data = await asyncio.to_thread(read_part, path, start)
            part = await client.upload_part(
                Bucket=s3_client.bucket,
                Key=key,
                UploadId=upload_id,
                PartNumber=number,
                Body=data,
            )
        return {"PartNumber": number, "ETag": part["ETag"]}

    starts = range(0, path.stat().st_size, PART_SIZE)
    return await asyncio.gather(
        *(upload_part(number, start) for number, start in enumerate(starts, start=1))
    )


async def upload_file(
    key: str, path: Path, md5: str, semaphore: asyncio.Semaphore
) -> None:
    """Upload `path` to `key`, in concurrent parts when bigger than one part,
    with its MD5 as object metadata."""
    kwargs = {
        "Bucket": s3_client.bucket,
        "Key": key,
        "ACL": "public-read",
        "ContentType": s3_client._get_mime_type(path.name),
        "Metadata": {MD5_METADATA: md5},
    }
    async with s3_client._client() as client:
        if path.stat().st_size <= PART_SIZE:
            async with semaphore:
                await client.put_object(Body=path.read_bytes(), **kwargs)
            return
        upload_id = (await client.create_multipart_upload(**kwargs))["UploadId"]
        try:
            parts = await upload_parts(client, key, path, upload_id, semaphore)
            await client.complete_multipart_upload(
                Bucket=s3_client.bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
        except BaseException:
            await client.abort_multipart_upload(
                Bucket=s3_client.bucket, Key=key, UploadId=upload_id
            )
            raise


async def dataset_file(
    identifier: str,
    dataset: DatasetDraft,
    path: Path,
    cache: Md5Cache,
    semaphore: asyncio.Semaphore,
) -> tuple[dict, bool]:
    """FileRef of a dataset file in the study draft, uploading it unless the
    draft already holds the same content. Returns (ref, skipped)."""
    key = draft_file_key(identifier, dataset, path)
    md5 = await asyncio.to_thread(cache.get, path)
    skipped = await is_uploaded(key, path, md5)
    if not skipped:
        started = time.perf_counter()
        await upload_file(key, path, md5, semaphore)
        size = path.stat().st_size
        if size > PART_SIZE:
            elapsed = time.perf_counter() - started
            print(
                f"    uploaded {path.name}: {size / 1e6:.0f} MB "
                f"in {elapsed:.0f}s ({size / elapsed / 1e6:.1f} MB/s)",
                flush=True,
            )
    ref = FileRef(
        name=path.name,
        path=urllib.parse.quote(key),
        size=path.stat().st_size,
        mime_type=s3_client._get_mime_type(path.name),
    )
    return ref.model_dump(), skipped


async def dataset_folders(
    identifier: str, seed: SeedStudy, cache: Md5Cache
) -> tuple[dict[int, dict], int]:
    """Folder of every dataset draft, all files uploaded concurrently.
    Returns folders by dataset id and the number of skipped uploads."""
    semaphore = asyncio.Semaphore(UPLOAD_CONCURRENCY)
    jobs = [(dataset, path) for dataset, files in seed.dataset_files for path in files]
    results = await asyncio.gather(
        *(dataset_file(identifier, d, p, cache, semaphore) for d, p in jobs)
    )
    folders: dict[int, dict] = {}
    skipped = 0
    for (dataset, _), (ref, was_skipped) in zip(jobs, results):
        folder = folders.setdefault(
            id(dataset),
            {
                "name": dataset.name,
                "path": s3_client.to_s3_path(
                    f"draft/{identifier}/files/{dataset.name}"
                ),
                "is_file": False,
                "children": [],
            },
        )
        folder["children"].append(ref)
        skipped += was_skipped
    return folders, skipped


async def delete_stale_draft_files(identifier: str, keep: set[str]) -> None:
    """Remove draft files of a previous run that are not part of this import,
    so they are not published. study.json is overwritten by the draft service."""
    for key in await s3_client.list_files(f"draft/{identifier}/"):
        if key not in keep and not key.endswith("/study.json"):
            await s3_client.delete_file(key)


async def publish(engine, seed: SeedStudy, cache: Md5Cache) -> int:
    """Replace the study draft with SEED_DATA content, then publish it.
    Returns the number of files skipped because unchanged in S3."""
    identifier = seed.draft.identifier
    await delete_stale_draft_files(
        identifier,
        keep={
            draft_file_key(identifier, dataset, path)
            for dataset, files in seed.dataset_files
            for path in files
        },
    )

    # Only datasets with a matched file are published, with the processed files
    folders, skipped = await dataset_folders(identifier, seed, cache)
    seed.draft.datasets = []
    for dataset, _ in seed.dataset_files:
        dataset.folder = folders[id(dataset)]
        seed.draft.datasets.append(dataset)

    draft = await StudyDraftService().createOrUpdate(seed.draft)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        await StudyService(session).save(draft)
    return skipped


def study_folders(identifiers: list[str]) -> list[Path]:
    """Study folders of SEED_DATA, all of them when `identifiers` is empty."""
    if not SEED_DATA.is_dir():
        raise FileNotFoundError(f"{SEED_DATA} does not exist")
    folders = [p for p in visible_entries(SEED_DATA) if p.is_dir()]
    if not identifiers:
        return folders
    missing = set(identifiers) - {p.name for p in folders}
    if missing:
        raise FileNotFoundError(f"no study folder in {SEED_DATA} for {sorted(missing)}")
    return [p for p in folders if p.name in identifiers]


async def run(check_only: bool, identifiers: list[str]) -> list[tuple[str, str]]:
    """Process the selected study folders (all when `identifiers` is empty),
    returning (folder, error) for failures."""
    if not check_only and "prod" in config.S3_PATH_PREFIX:
        raise RuntimeError(
            f"Refusing to seed into S3_PATH_PREFIX={config.S3_PATH_PREFIX}"
        )

    engine = create_async_engine(config.DB_URL)
    cache = Md5Cache(MD5_CACHE)
    failures = []
    folders = study_folders(identifiers)
    for i, folder in enumerate(folders, start=1):
        print(f"[{i}/{len(folders)}] {folder.name} ...", flush=True)
        try:
            seed = load_study(folder)
            skipped = 0 if check_only else await publish(engine, seed, cache)
            for warning in seed.warnings:
                print(f"    WARNING: {warning}")
            total_files = sum(len(f) for _, f in seed.dataset_files)
            print(
                f"    ok: {seed.draft.name} "
                f"({len(seed.dataset_files)} dataset(s), {total_files} file(s)"
                + (f", {skipped} already in S3" if skipped else "")
                + ")"
            )
        except Exception as e:
            traceback.print_exc()
            failures.append((folder.name, f"{type(e).__name__}: {e}"))
            print(f"    FAILED: {failures[-1][1]}")
        finally:
            if not check_only:
                cache.save()
    await engine.dispose()
    await s3_client.close()
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="validate only, write nothing"
    )
    parser.add_argument(
        "identifiers",
        nargs="*",
        metavar="identifier",
        help="only import these studies (default: all of SEED_DATA)",
    )
    args = parser.parse_args()

    failures = asyncio.run(run(args.check, args.identifiers))
    total = len(study_folders(args.identifiers))
    action = "valid" if args.check else "imported"
    print(f"\n{total - len(failures)}/{total} studies {action}")
    for name, error in failures:
        print(f"  FAILED {name}: {error}")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
