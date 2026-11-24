"""`GET /stats/schema`: the static descriptor a client loads once."""

from api.models.explore import Benchmark, ExploreSchema, Parameter
from api.services.explore.dimensions import DIMENSIONS
from api.services.parameter import ParameterService
from sqlmodel.ext.asyncio.session import AsyncSession

# numeric catalog columns a relationship query may take as `y`
METRICS = [
    "space.occupancy_density",
    "space.occupancy_number",
    "space.floor_area",
    "space.space_volume",
    "building.airtightness",
    "building.construction_year",
    "building.altitude",
]

# a reference's averaging -> the query grain whose values compare with it
AVERAGING_GRAINS = {"hour": "hour", "day": "day", "long_term": "space"}


def _menu_order(b: Benchmark) -> tuple:
    """The default first, then worldwide references, then by region."""
    return (
        not b.is_default,
        b.region != "Worldwide",
        b.region.casefold(),
        b.source.casefold(),
        b.value,
    )


async def explore_schema(session: AsyncSession, version: int) -> ExploreSchema:
    service = ParameterService(session)
    benchmarks: dict[str, list[Benchmark]] = {}
    for b in await service.benchmarks():
        benchmarks.setdefault(b.parameter, []).append(
            Benchmark(**b.model_dump(), grain=AVERAGING_GRAINS[b.averaging])
        )
    parameters = [
        Parameter(
            slug=p.slug,
            label=p.label,
            reference=p.reference,
            unit=p.unit,
            benchmarks=sorted(benchmarks.get(p.slug, []), key=_menu_order),
        )
        for p in await service.all()
    ]
    return ExploreSchema(
        dimensions=[d.describe() for d in DIMENSIONS.values()],
        parameters=parameters,
        metrics=METRICS,
        version=version,
    )
