"""The parameter dictionary: versioned CSVs in api/data, mirrored into the
`parameter` and `benchmark` tables at boot and at data upload."""

import csv
import json
from collections import Counter
from importlib.resources import files
from pathlib import Path

from api.db import AsyncSession
from api.models.measurement import Benchmark, Parameter
from api.services.catalog_version import CatalogVersionService
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col, delete, select

PARAMETERS_CSV = Path(str(files("api") / "data/parameters.csv"))
BENCHMARKS_CSV = Path(str(files("api") / "data/benchmarks.csv"))
# hour and day compare with hourly and daily means; long_term with the mean
# of each space over the whole period (annual guidelines)
AVERAGINGS = ("hour", "day", "long_term")
BENCHMARK_REQUIRED = (
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


def read_parameters(path: Path = PARAMETERS_CSV) -> list[Parameter]:
    """Parse the dictionary CSV, refusing any row that is not fully specified."""
    parameters = []
    with path.open(encoding="utf-8") as stream:
        for line, row in enumerate(csv.DictReader(stream), start=2):
            parameters.append(_parse_parameter(path, line, row))
    if not parameters:
        raise ValueError(f"{path.name} has no parameter")
    return parameters


def _parse_parameter(path: Path, line: int, row: dict) -> Parameter:
    missing = [k for k in ("slug", "label", "reference", "unit") if not row.get(k)]
    if missing:
        raise ValueError(f"{path.name}:{line}: missing {missing}")
    try:
        conversions = json.loads(row["conversions"])
    except (json.JSONDecodeError, TypeError) as e:
        raise ValueError(f"{path.name}:{line}: conversions is not JSON: {e}")
    canonical = conversions.get(row["unit"])
    if canonical is None or canonical.get("factor") != 1 or canonical.get("offset"):
        raise ValueError(
            f"{path.name}:{line}: canonical unit '{row['unit']}' must map to factor 1"
        )
    for unit, conversion in conversions.items():
        if not isinstance(conversion.get("factor"), (int, float)):
            raise ValueError(f"{path.name}:{line}: unit '{unit}' has no factor")
    return Parameter(
        slug=row["slug"],
        label=row["label"],
        reference=row["reference"],
        unit=row["unit"],
        conversions=conversions,
    )


def read_benchmarks(
    path: Path = BENCHMARKS_CSV, parameters: dict[str, Parameter] | None = None
) -> list[Benchmark]:
    """Parse the benchmarks CSV: values in the parameter's canonical unit,
    unique ids, exactly one default per parameter."""
    parameters = parameters or {p.slug: p for p in read_parameters()}
    benchmarks: dict[str, Benchmark] = {}
    with path.open(encoding="utf-8") as stream:
        for line, row in enumerate(csv.DictReader(stream), start=2):
            benchmark = _parse_benchmark(path, line, row, parameters)
            if benchmark.id in benchmarks:
                raise ValueError(f"{path.name}:{line}: duplicate id '{benchmark.id}'")
            benchmarks[benchmark.id] = benchmark
    defaults = Counter(b.parameter for b in benchmarks.values() if b.is_default)
    for slug in sorted({b.parameter for b in benchmarks.values()}):
        if defaults[slug] != 1:
            raise ValueError(
                f"{path.name}: '{slug}' has {defaults[slug]} defaults, expected 1"
            )
    return list(benchmarks.values())


def _parse_benchmark(
    path: Path, line: int, row: dict, parameters: dict[str, Parameter]
) -> Benchmark:
    missing = [k for k in BENCHMARK_REQUIRED if not row.get(k)]
    if missing:
        raise ValueError(f"{path.name}:{line}: missing {missing}")
    parameter = parameters.get(row["parameter"])
    if parameter is None:
        raise ValueError(f"{path.name}:{line}: unknown parameter '{row['parameter']}'")
    if row["unit"] != parameter.unit:
        raise ValueError(
            f"{path.name}:{line}: unit must be '{parameter.unit}'"
            f" (canonical), got '{row['unit']}'"
        )
    if row["averaging"] not in AVERAGINGS:
        raise ValueError(f"{path.name}:{line}: averaging not in {AVERAGINGS}")
    if row["is_default"] not in ("true", "false"):
        raise ValueError(f"{path.name}:{line}: is_default must be true or false")
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


def _parameter_key(p: Parameter) -> tuple:
    return (p.label, p.reference, p.unit, json.dumps(p.conversions, sort_keys=True))


class ParameterService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def sync(self) -> int:
        """Upsert the CSV dictionary into the database. Parameters are never
        deleted (measurements reference them); benchmarks are replaced. The
        catalog version is bumped when anything changed, so cached explore
        results (the schema carries the dictionary) do not outlive it.
        Returns the number of parameters."""
        parameters = read_parameters()
        benchmarks = read_benchmarks(parameters={p.slug: p for p in parameters})
        if await self._mirrored(parameters, benchmarks):
            return len(parameters)
        statement = insert(Parameter).values([p.model_dump() for p in parameters])
        statement = statement.on_conflict_do_update(
            index_elements=[Parameter.slug],
            set_={
                "label": statement.excluded.label,
                "reference": statement.excluded.reference,
                "unit": statement.excluded.unit,
                "conversions": statement.excluded.conversions,
            },
        )
        await self.session.exec(statement)
        await self.session.exec(delete(Benchmark))
        self.session.add_all(benchmarks)
        await CatalogVersionService(self.session).bump()
        return len(parameters)

    async def _mirrored(
        self, parameters: list[Parameter], benchmarks: list[Benchmark]
    ) -> bool:
        """Whether the database already holds exactly the CSV contents."""
        stored = {p.slug: p for p in await self.all()}
        if any(
            stored.get(p.slug) is None
            or _parameter_key(stored[p.slug]) != _parameter_key(p)
            for p in parameters
        ):
            return False
        stored_benchmarks = {b.id: b.model_dump() for b in await self.benchmarks()}
        return stored_benchmarks == {b.id: b.model_dump() for b in benchmarks}

    async def all(self) -> list[Parameter]:
        result = await self.session.exec(
            select(Parameter).order_by(col(Parameter.slug))
        )
        return list(result.all())

    async def benchmarks(self) -> list[Benchmark]:
        result = await self.session.exec(
            select(Benchmark).order_by(col(Benchmark.parameter), col(Benchmark.id))
        )
        return list(result.all())
