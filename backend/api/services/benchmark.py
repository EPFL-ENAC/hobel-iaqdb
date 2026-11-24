"""Reference values (guidelines, legal limits, design criteria) in the
`benchmark` table. The backend only reads them: api/scripts/import_benchmarks.py
fills the table of one database from a benchmarks CSV
(docs/202-reference-values.md)."""

import csv
from collections import Counter
from pathlib import Path
from typing import Iterable

from api.db import AsyncSession
from api.models.measurement import Benchmark, Parameter
from api.services.catalog_version import CatalogVersionService
from sqlmodel import col, delete, select

# hour and day compare with hourly and daily means; long_term with the mean
# of each space over the whole period (annual guidelines)
AVERAGINGS = ("hour", "day", "long_term")
# the columns of a benchmarks CSV, in order
COLUMNS = (
    "id",
    "parameter",
    "is_default",
    "source",
    "institution",
    "year",
    "region",
    "limit_type",
    "legal_status",
    "setting",
    "averaging",
    "period",
    "value",
    "unit",
    "qualifier",
    "url",
    "note",
)
REQUIRED = (
    "id",
    "parameter",
    "is_default",
    "source",
    "institution",
    "region",
    "limit_type",
    "averaging",
    "period",
    "value",
    "unit",
)


def read_csv(path: Path) -> list[dict]:
    """The rows of a benchmarks CSV, refusing columns other than COLUMNS."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if sorted(reader.fieldnames or ()) != sorted(COLUMNS):
            raise ValueError(
                f"{path.name}: columns must be {list(COLUMNS)},"
                f" got {reader.fieldnames}"
            )
        return list(reader)


def parse_benchmarks(
    rows: Iterable[dict], parameters: dict[str, Parameter]
) -> list[Benchmark]:
    """Text rows as benchmarks: values in the parameter's canonical unit,
    unique ids, exactly one default per parameter."""
    benchmarks: dict[str, Benchmark] = {}
    for row in rows:
        benchmark = _parse_benchmark(row, parameters)
        if benchmark.id in benchmarks:
            raise ValueError(f"duplicate id '{benchmark.id}'")
        benchmarks[benchmark.id] = benchmark
    defaults = Counter(b.parameter for b in benchmarks.values() if b.is_default)
    for slug in sorted({b.parameter for b in benchmarks.values()}):
        if defaults[slug] != 1:
            raise ValueError(f"'{slug}' has {defaults[slug]} defaults, expected 1")
    return list(benchmarks.values())


def _parse_benchmark(row: dict, parameters: dict[str, Parameter]) -> Benchmark:
    where = row.get("id") or "a row without id"
    missing = [k for k in REQUIRED if not row.get(k)]
    if missing:
        raise ValueError(f"{where}: missing {missing}")
    parameter = parameters.get(row["parameter"])
    if parameter is None:
        raise ValueError(f"{where}: unknown parameter '{row['parameter']}'")
    if row["unit"] != parameter.unit:
        raise ValueError(
            f"{where}: unit must be '{parameter.unit}'"
            f" (canonical), got '{row['unit']}'"
        )
    if row["averaging"] not in AVERAGINGS:
        raise ValueError(f"{where}: averaging not in {AVERAGINGS}")
    if row["is_default"] not in ("true", "false"):
        raise ValueError(f"{where}: is_default must be true or false")
    return Benchmark(
        id=row["id"],
        parameter=parameter.slug,
        is_default=row["is_default"] == "true",
        source=row["source"],
        institution=row["institution"],
        year=int(row["year"]) if row.get("year") else None,
        region=row["region"],
        limit_type=row["limit_type"],
        legal_status=row.get("legal_status") or None,
        setting=row.get("setting") or None,
        averaging=row["averaging"],
        period=row["period"],
        value=float(row["value"]),
        unit=row["unit"],
        qualifier=row.get("qualifier") or None,
        url=row.get("url") or None,
        note=row.get("note") or None,
    )


class BenchmarkService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def all(self) -> list[Benchmark]:
        result = await self.session.exec(
            select(Benchmark).order_by(col(Benchmark.parameter), col(Benchmark.id))
        )
        return list(result.all())

    async def replace(self, benchmarks: list[Benchmark]) -> bool:
        """Make the table hold exactly `benchmarks`, and bump the catalog
        version so no cached schema keeps the old references. Returns False,
        and writes nothing, when the table already holds them. The caller
        commits."""
        stored = {b.id: b.model_dump() for b in await self.all()}
        if stored == {b.id: b.model_dump() for b in benchmarks}:
            return False
        await self.session.exec(delete(Benchmark))
        self.session.add_all(benchmarks)
        await CatalogVersionService(self.session).bump()
        return True
