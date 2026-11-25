"""Measurement load of a published study: its dataset files are streamed
from S3 one at a time and loaded into the hypertable. Runs as a background
task of the publish route; each dataset's `summary_status` shows the outcome."""

import tempfile
from pathlib import Path

from api.models.catalog import Dataset, Study
from api.services.catalog_version import CatalogVersionService
from api.services.measurement import MeasurementService, measurement_write_lock
from api.services.s3 import download_object, s3_client
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


def csv_keys(dataset: Dataset, identifier: str) -> list[tuple[str, str]]:
    """(S3 key, file name) of the dataset's processed CSV files, and zips of
    them: a contributor uploads one file per dataset, so several CSVs come
    as a zip. Names and paths are the contributor's: a file is only read from
    the published files of the study, and its name never has a folder."""
    children = (dataset.folder or {}).get("children") or []
    folder = s3_client.to_s3_key(f"pub/{identifier}/")
    keys = []
    for child in children:
        name = Path(child["name"]).name
        if not name.lower().endswith((".csv", ".zip")):
            continue
        key = s3_client.to_s3_key(child["path"])
        if not key.startswith(folder) or ".." in key.split("/"):
            raise ValueError(f"{name} is not a published file of the study")
        keys.append((key, name))
    return keys


async def load_dataset(
    service: MeasurementService, dataset: Dataset, identifier: str
) -> None:
    try:
        keys = csv_keys(dataset, identifier)
    except ValueError as e:
        await service.fail(dataset.id, str(e))
        raise
    if not keys:
        await service.fail(dataset.id, "no CSV file in the dataset folder")
        raise ValueError(f"dataset {dataset.name}: no CSV file")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            paths = []
            for i, (key, name) in enumerate(keys):
                # own folder: files may share a name
                folder = Path(tmp) / str(i)
                folder.mkdir()
                paths.append(await download_object(key, folder / name))
        except Exception as e:
            await service.fail(dataset.id, f"download failed: {e}")
            raise
        await service.load(dataset.id, paths)


async def refresh_and_bump(engine: AsyncEngine) -> None:
    """Refresh the continuous aggregates, then bump the catalog version so
    that explore results computed from the stale aggregates in the meantime
    are dropped. The route bumps once more on commit, for the catalog itself."""
    await MeasurementService(engine).refresh_all()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        await CatalogVersionService(session).bump()
        await session.commit()


async def load_published_study(engine: AsyncEngine, study_id: int) -> None:
    """Load every dataset of the study; the aggregates are refreshed even
    when a load fails, since publishing replaced the previous rows."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        identifier = (
            await session.exec(select(Study.identifier).where(Study.id == study_id))
        ).one()
        datasets = (
            await session.exec(select(Dataset).where(Dataset.study_id == study_id))
        ).all()
    service = MeasurementService(engine)
    errors = []
    async with measurement_write_lock(engine):
        for dataset in datasets:
            try:
                await load_dataset(service, dataset, identifier)
            except Exception as e:
                errors.append(f"{dataset.name}: {e}")
        await refresh_and_bump(engine)
    if errors:
        raise RuntimeError(
            f"study {study_id}: {len(errors)} dataset(s) failed: {errors}"
        )


async def refresh_after_delete(engine: AsyncEngine) -> None:
    """Deleting catalog rows cascades to `measurement`; the continuous
    aggregates only follow on refresh."""
    async with measurement_write_lock(engine):
        await refresh_and_bump(engine)
