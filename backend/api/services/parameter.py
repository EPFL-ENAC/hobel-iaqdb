"""The parameter dictionary: a versioned CSV in api/data, mirrored into the
`parameter` table at boot and at data upload. The reference values are not
in it: api/scripts/import_benchmarks.py writes them to the database."""

import csv
import json
from importlib.resources import files
from pathlib import Path

from api.db import AsyncSession
from api.models.measurement import Parameter
from api.services.catalog_version import CatalogVersionService
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col, select

PARAMETERS_CSV = Path(str(files("api") / "data/parameters.csv"))


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


def _parameter_key(p: Parameter) -> tuple:
    return (p.label, p.reference, p.unit, json.dumps(p.conversions, sort_keys=True))


class ParameterService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def sync(self) -> int:
        """Upsert the CSV dictionary into the database. Parameters are never
        deleted (measurements and benchmarks reference them). The catalog
        version is bumped when anything changed, so cached explore results
        (the schema carries the dictionary) do not outlive it. Returns the
        number of parameters."""
        parameters = read_parameters()
        stored = {p.slug: p for p in await self.all()}
        if all(
            p.slug in stored and _parameter_key(stored[p.slug]) == _parameter_key(p)
            for p in parameters
        ):
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
        await CatalogVersionService(self.session).bump()
        return len(parameters)

    async def all(self) -> list[Parameter]:
        result = await self.session.exec(
            select(Parameter).order_by(col(Parameter.slug))
        )
        return list(result.all())
