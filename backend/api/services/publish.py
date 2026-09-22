"""Measurement load of a published study: its dataset files are streamed
from S3 one at a time and loaded into the hypertable. Runs as a background
task of the publish route; each dataset's `summary_status` shows the outcome."""

import tempfile
import urllib.parse
from pathlib import Path

from api.models.catalog import Dataset
from api.services.measurement import MeasurementService
from api.services.s3 import download_object
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


def csv_keys(dataset: Dataset) -> list[tuple[str, str]]:
    """(S3 key, file name) of the dataset's processed CSV files."""
    children = (dataset.folder or {}).get("children") or []
    return [
        (urllib.parse.unquote(child["path"]), child["name"])
        for child in children
        if child["name"].lower().endswith(".csv")
    ]


async def load_dataset(service: MeasurementService, dataset: Dataset) -> None:
    keys = csv_keys(dataset)
    if not keys:
        await service.fail(dataset.id, "no CSV file in the dataset folder")
        raise ValueError(f"dataset {dataset.name}: no CSV file")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            paths = [await download_object(key, Path(tmp) / name) for key, name in keys]
        except Exception as e:
            await service.fail(dataset.id, f"download failed: {e}")
            raise
        await service.load(dataset.id, paths)


async def load_published_study(engine: AsyncEngine, study_id: int) -> None:
    """Load every dataset of the study; the aggregates are refreshed even
    when a load fails, since publishing replaced the previous rows."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        datasets = (
            await session.exec(select(Dataset).where(Dataset.study_id == study_id))
        ).all()
    service = MeasurementService(engine)
    errors = []
    for dataset in datasets:
        try:
            await load_dataset(service, dataset)
        except Exception as e:
            errors.append(f"{dataset.name}: {e}")
    await service.refresh_all()
    if errors:
        raise RuntimeError(f"study {study_id}: {len(errors)} dataset(s) failed: {errors}")


async def refresh_after_delete(engine: AsyncEngine) -> None:
    """Deleting catalog rows cascades to `measurement`; the continuous
    aggregates only follow on refresh."""
    await MeasurementService(engine).refresh_all()
