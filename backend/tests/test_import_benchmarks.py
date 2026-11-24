"""The benchmarks CSV import into a database (docs/202-reference-values.md)."""

import csv
from pathlib import Path

import pytest
from api.config import config
from api.scripts import import_benchmarks
from api.services.benchmark import COLUMNS, BenchmarkService
from api.services.catalog_version import CatalogVersionService
from tests.test_benchmarks import benchmark_row


async def _stored(session) -> dict[str, float]:
    await session.rollback()  # see what the script committed
    return {b.id: b.value for b in await BenchmarkService(session).all()}


async def test_import_replaces_the_references(tmp_path, session, monkeypatch):
    def write(*rows) -> Path:
        path = tmp_path / "benchmarks.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    path = write(benchmark_row("a"), benchmark_row("b", "false"))
    await import_benchmarks.run(path, check_only=True)
    assert await _stored(session) == {}
    await import_benchmarks.run(path)
    assert await _stored(session) == {"a": 1200, "b": 1200}
    assert await CatalogVersionService(session).get() == 2
    # the same CSV again: nothing to invalidate
    await import_benchmarks.run(path)
    assert await CatalogVersionService(session).get() == 2
    # a new CSV replaces every row
    path = write(benchmark_row("c", value="1000"))
    await import_benchmarks.run(path)
    assert await _stored(session) == {"c": 1000}
    assert await CatalogVersionService(session).get() == 3
    # a refused CSV keeps the current references
    path = write(benchmark_row("d", unit="ppb"))
    with pytest.raises(ValueError, match="d: unit must be 'ppm'"):
        await import_benchmarks.run(path)
    path.write_text("id,parameter,value\nd,co2,1200\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columns must be"):
        await import_benchmarks.run(path)
    assert await _stored(session) == {"c": 1000}
    monkeypatch.setattr(config, "S3_PATH_PREFIX", "iaqdb/prod/")
    with pytest.raises(RuntimeError, match="--allow-prod"):
        await import_benchmarks.run(path)
