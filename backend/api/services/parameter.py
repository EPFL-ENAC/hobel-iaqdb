"""The parameter dictionary: versioned CSVs in api/data, mirrored into the
`parameter` and `benchmark` tables at boot and at seed."""

import csv
import json
from importlib.resources import files
from pathlib import Path

from api.db import AsyncSession
from api.models.measurement import Benchmark, Parameter
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col, delete, select

PARAMETERS_CSV = Path(str(files("api") / "data/parameters.csv"))
BENCHMARKS_CSV = Path(str(files("api") / "data/benchmarks.csv"))
AVERAGINGS = ("hour", "day")


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
    """Parse the benchmarks CSV; values must be in the parameter's canonical unit."""
    parameters = parameters or {p.slug: p for p in read_parameters()}
    benchmarks = []
    with path.open(encoding="utf-8") as stream:
        for line, row in enumerate(csv.DictReader(stream), start=2):
            parameter = parameters.get(row.get("parameter", ""))
            if parameter is None:
                raise ValueError(
                    f"{path.name}:{line}: unknown parameter '{row.get('parameter')}'"
                )
            if row.get("unit") != parameter.unit:
                raise ValueError(
                    f"{path.name}:{line}: unit must be '{parameter.unit}'"
                    f" (canonical), got '{row.get('unit')}'"
                )
            if row.get("averaging") not in AVERAGINGS:
                raise ValueError(f"{path.name}:{line}: averaging not in {AVERAGINGS}")
            benchmarks.append(
                Benchmark(
                    parameter=parameter.slug,
                    source=row["source"],
                    averaging=row["averaging"],
                    value=float(row["value"]),
                    unit=row["unit"],
                    note=row.get("note") or None,
                )
            )
    return benchmarks


class ParameterService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def sync(self) -> int:
        """Upsert the CSV dictionary into the database. Parameters are never
        deleted (measurements reference them); benchmarks are replaced.
        Returns the number of parameters."""
        parameters = read_parameters()
        benchmarks = read_benchmarks(parameters={p.slug: p for p in parameters})
        statement = insert(Parameter).values(
            [p.model_dump() for p in parameters]
        )
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
        return len(parameters)

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
