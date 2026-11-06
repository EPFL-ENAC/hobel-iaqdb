"""Dimension registry (design §5) and the FROM clause it drives.

A dimension is a key the client groups by. Each one knows which catalog
entity it reads, how a bucket key becomes a filter criterion (`filter_path`)
and what to drill into next. Adding a dimension is one entry here."""

from dataclasses import dataclass
from typing import Any, Callable

from api.models.explore import Dimension
from fastapi import HTTPException
from sqlalchemy import case, extract, func

# The Köppen-Geiger climate zones of each main group: A tropical, B dry
# (arid and semiarid), C temperate, D continental, E polar.
KOPPEN_GROUPS: dict[str, tuple[str, ...]] = {
    "A": ("Af", "Am", "Aw"),
    "B": ("BWh", "BWk", "BSh", "BSk"),
    "C": ("Csa", "Csb", "Csc", "Cwa", "Cwb", "Cwc", "Cfa", "Cfb", "Cfc"),
    "D": (
        "Dsa", "Dsb", "Dsc", "Dsd",
        "Dwa", "Dwb", "Dwc", "Dwd",
        "Dfa", "Dfb", "Dfc", "Dfd",
    ),  # fmt: skip
    "E": ("ET", "EF"),
}
ZONE_GROUPS = {zone: group for group, zones in KOPPEN_GROUPS.items() for zone in zones}


def climate_group_of(climate_zone: Any) -> Any:
    """The group of a zone, from the mapping; null for a zone outside it
    ("NA", at sea)."""
    return case(ZONE_GROUPS, value=climate_zone)


class Frame:
    """A FROM clause built lazily: entities are joined the first time a
    dimension or a filter needs them, as LEFT OUTER JOINs so a missing
    building or space becomes the `null` bucket."""

    def __init__(
        self,
        root_entity: str,
        root: Any,
        available: dict[str, tuple[Any, Any, tuple[str, ...]]],
        time: Any = None,
        parameter: Any = None,
    ):
        # joins chain on the table; mapped classes stay the column source
        self.select_from = getattr(root, "__table__", root)
        self.available = available
        self.used: dict[str, Any] = {root_entity: root}
        self.time = time
        self.parameter = parameter

    def use(self, entity: str) -> Any:
        if entity in self.used:
            return self.used[entity]
        if entity not in self.available:
            raise HTTPException(
                status_code=422, detail=f"'{entity}' is not reachable from this query"
            )
        target, onclause, dependencies = self.available[entity]
        for dependency in dependencies:
            self.use(dependency)
        self.select_from = self.select_from.outerjoin(target, onclause)
        self.used[entity] = target
        return target

    def time_column(self) -> Any:
        if self.time is None:
            raise HTTPException(
                status_code=422, detail="time dimensions need a measurement query"
            )
        return self.time

    def parameter_column(self) -> Any:
        if self.parameter is None:
            raise HTTPException(
                status_code=422, detail="'parameter' needs a measurement query"
            )
        return self.parameter


@dataclass(frozen=True)
class DimensionSpec:
    key: str
    label: str
    entity: str
    filter_path: str | None
    drill_to: str | None
    kind: str
    column: Callable[[Frame], Any]
    # only meaningful at this grain (hour_of_day needs hourly buckets)
    grain: str | None = None

    def describe(self) -> Dimension:
        return Dimension(
            key=self.key,
            label=self.label,
            entity=self.entity,
            filter_path=self.filter_path,
            drill_to=self.drill_to,
            kind=self.kind,
        )


def _category(key, label, entity, attr, filter_path, drill_to) -> DimensionSpec:
    return DimensionSpec(
        key,
        label,
        entity,
        filter_path,
        drill_to,
        "category",
        lambda f: getattr(f.use(entity), attr),
    )


def _band(key, label, entity, attr, step) -> DimensionSpec:
    """A number in bands of `step`, keyed by their lower bound ("250"): for
    histograms, so no filter path (the filters take ranges)."""
    return DimensionSpec(
        key,
        label,
        entity,
        None,
        None,
        "category",
        lambda f: func.floor(getattr(f.use(entity), attr) / step) * step,
    )


def _time(key, label, trunc, drill_to) -> DimensionSpec:
    return DimensionSpec(
        key,
        label,
        "time",
        "from",
        drill_to,
        "time",
        lambda f: func.date_trunc(trunc, f.time_column()),
    )


DIMENSIONS: dict[str, DimensionSpec] = {
    d.key: d
    for d in (
        _category("study", "Study", "study", "identifier", "identifier", "dataset"),
        _category("dataset", "Dataset", "dataset", "id", "$dataset.id", None),
        _category(
            "country", "Country", "building", "country", "$building.country", "city"
        ),
        _category("city", "City", "building", "city", "$building.city", "study"),
        DimensionSpec(
            "climate_group",
            "Climate group",
            "building",
            # no column of the building: see filters.DERIVED_FIELDS
            "$building.climate_group",
            "climate_zone",
            "category",
            lambda f: climate_group_of(f.use("building").climate_zone),
        ),
        _category(
            "climate_zone",
            "Climate zone",
            "building",
            "climate_zone",
            "$building.climate_zone",
            "country",
        ),
        _category(
            "building_type",
            "Building type",
            "building",
            "type",
            "$building.type",
            "country",
        ),
        _category(
            "ventilation",
            "Mechanical ventilation",
            "building",
            "mechanical_ventilation",
            "$building.mechanical_ventilation",
            "ventilation_type",
        ),
        _category(
            "ventilation_type",
            "Ventilation type",
            "space",
            "mechanical_ventilation_type",
            "$space.mechanical_ventilation_type",
            "space_type",
        ),
        _category(
            "outdoor_env",
            "Outdoor environment",
            "building",
            "outdoor_env",
            "$building.outdoor_env",
            None,
        ),
        _category(
            "age_group",
            "Occupant age group",
            "building",
            "age_group",
            "$building.age_group",
            None,
        ),
        _category(
            "socioeconomic_status",
            "Socioeconomic status",
            "building",
            "socioeconomic_status",
            "$building.socioeconomic_status",
            None,
        ),
        _band("altitude_band", "Altitude", "building", "altitude", 250),
        _band(
            "construction_decade",
            "Construction decade",
            "building",
            "construction_year",
            10,
        ),
        _category("space_type", "Space type", "space", "type", "$space.type", None),
        _category(
            "occupancy", "Occupancy", "space", "occupancy", "$space.occupancy", None
        ),
        DimensionSpec(
            "parameter",
            "Parameter",
            "parameter",
            "parameters",
            None,
            "category",
            lambda f: f.parameter_column(),
        ),
        _time("year", "Year", "year", "month"),
        _time("month", "Month", "month", "day"),
        _time("day", "Day", "day", None),
        DimensionSpec(
            "month_of_year",
            "Month of year",
            "time",
            None,
            None,
            "category",
            lambda f: extract("month", f.time_column()),
        ),
        DimensionSpec(
            "hour_of_day",
            "Hour of day",
            "time",
            None,
            None,
            "category",
            lambda f: extract("hour", f.time_column()),
            grain="hour",
        ),
    )
}


def resolve(keys: list[str], grain: str | None) -> list[DimensionSpec]:
    specs = []
    for key in keys:
        spec = DIMENSIONS.get(key)
        if spec is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"unknown dimension '{key}',"
                    f" expected one of {sorted(DIMENSIONS)}"
                ),
            )
        if spec.grain and spec.grain != grain:
            raise HTTPException(
                status_code=422, detail=f"'{key}' requires grain={spec.grain}"
            )
        specs.append(spec)
    return specs
