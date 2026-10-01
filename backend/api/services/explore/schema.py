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


async def explore_schema(session: AsyncSession, version: int) -> ExploreSchema:
    service = ParameterService(session)
    benchmarks: dict[str, list[Benchmark]] = {}
    for b in await service.benchmarks():
        benchmarks.setdefault(b.parameter, []).append(
            Benchmark(
                id=b.id,
                parameter=b.parameter,
                source=b.source,
                averaging=b.averaging,
                value=b.value,
                unit=b.unit,
                note=b.note,
            )
        )
    parameters = [
        Parameter(
            slug=p.slug,
            label=p.label,
            reference=p.reference,
            unit=p.unit,
            benchmarks=benchmarks.get(p.slug, []),
        )
        for p in await service.all()
    ]
    return ExploreSchema(
        dimensions=[d.describe() for d in DIMENSIONS.values()],
        parameters=parameters,
        metrics=METRICS,
        version=version,
    )
