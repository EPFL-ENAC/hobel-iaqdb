"""Contract of the explore routes (`/stats/*`), see docs/129-explore-charts-api.md."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Entity = Literal["studies", "buildings", "spaces", "datasets"]
Grain = Literal["day", "hour", "raw"]
Source = Literal["metadata", "measurements", "relationships"]
MetadataAgg = Literal["count", "availability"]
MeasurementAgg = Literal["coverage", "count", "stats", "exceedance"]
RelationshipAgg = Literal["pairs", "matrix"]
Method = Literal["pearson", "spearman"]
Agg = MetadataAgg | MeasurementAgg | RelationshipAgg

MAX_PARAMETERS = 10
MAX_DIMENSIONS = 2


def _split(value: str | list[str]) -> list[str]:
    """FastAPI hands a list with one entry per repeated query parameter;
    each entry may itself be comma-separated."""
    items = [value] if isinstance(value, str) else list(value)
    return [v.strip() for item in items for v in item.split(",") if v.strip()]


# ---- /stats/schema -------------------------------------------------------


class Dimension(BaseModel):
    key: str
    label: str
    entity: Literal["study", "building", "space", "dataset", "parameter", "time"]
    filter_path: str | None
    drill_to: str | None
    kind: Literal["category", "time"]


class Benchmark(BaseModel):
    id: int
    parameter: str
    source: str
    averaging: Literal["hour", "day"]
    value: float
    unit: str
    note: str | None = None


class Parameter(BaseModel):
    slug: str
    label: str
    reference: str
    unit: str
    benchmarks: list[Benchmark] = Field(default_factory=list)


class ExploreSchema(BaseModel):
    dimensions: list[Dimension]
    parameters: list[Parameter]
    metrics: list[str]
    version: int


# ---- query ---------------------------------------------------------------


class ExploreQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    filter: str | None = None
    from_: date | None = Field(default=None, alias="from")
    to: date | None = None
    parameters: list[str] = Field(default_factory=list, max_length=MAX_PARAMETERS)
    by: list[str] = Field(default_factory=list, max_length=MAX_DIMENSIONS)
    grain: Grain | None = None
    qualifier: list[str] = Field(default_factory=list)
    threshold: float | None = None
    entity: Entity | None = None
    fields: list[str] = Field(default_factory=list)
    x: str | None = None
    y: str | None = None
    method: Method = "pearson"
    agg: str | None = None

    @field_validator("parameters", "fields", "qualifier", mode="before")
    @classmethod
    def split_sorted(cls, value: str | list[str]) -> list[str]:
        return sorted(set(_split(value)))

    @field_validator("by", mode="before")
    @classmethod
    def split_ordered(cls, value: str | list[str]) -> list[str]:
        # order matters: it is the order of entries in bucket.key
        return list(dict.fromkeys(_split(value)))


# ---- envelope ------------------------------------------------------------


class Stats(BaseModel):
    mean: float
    sd: float | None
    min: float
    p05: float
    p25: float
    p50: float
    p75: float
    p95: float
    max: float


class Exceedance(BaseModel):
    threshold: float
    n_above: int
    share: float


class Coverage(BaseModel):
    n_datasets: int
    n_missing: int
    first_at: datetime | None
    last_at: datetime | None


class Availability(BaseModel):
    present: int
    total: int


class Fit(BaseModel):
    slope: float | None
    intercept: float | None
    r2: float | None
    r: float | None


class Bucket(BaseModel):
    key: list[str | None]
    n: int
    n_records: int | None = None
    stats: Stats | None = None
    exceedance: Exceedance | None = None
    coverage: Coverage | None = None
    availability: Availability | None = None
    fit: Fit | None = None
    points: list[tuple[float, float]] | None = None
    sampled: bool | None = None


class Meta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: Source
    agg: Agg
    grain: Grain | Literal["space", "entity"]
    dimensions: list[str]
    parameters: list[str]
    unit: str | None
    from_: date | None = Field(default=None, alias="from")
    to: date | None
    n: int
    n_records: int | None = None
    version: int
    available_parameters: list[str] | None = None


class ExploreResult(BaseModel):
    meta: Meta
    buckets: list[Bucket]
