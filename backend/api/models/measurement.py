"""Measurements and their dictionary.

`measurement` is a TimescaleDB hypertable (no primary key: the time column
partitions it), so it is declared as a Core table on the shared metadata
rather than a mapped model. `measurement_hour` and `measurement_day` are
continuous aggregates created by the migration; the query side declares them
in `api/services/explore/tables.py`.
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel
from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Parameter(SQLModel, table=True):
    """Dictionary of measured parameters, seeded from api/data/parameters.csv."""

    slug: str = Field(primary_key=True)
    label: str
    # ref in the taxonomy of variables (Variable.reference)
    reference: str
    # canonical unit, the one `measurement.value` is stored in
    unit: str
    # accepted source unit -> {"factor": f, "offset": o}: canonical = v*f + o
    conversions: Dict = Field(sa_column=Column(JSONB, nullable=False))


class Benchmark(SQLModel, table=True):
    """Guideline values (e.g. WHO AQG 2021), in the parameter's canonical unit."""

    id: Optional[int] = Field(default=None, primary_key=True)
    parameter: str = Field(foreign_key="parameter.slug", ondelete="CASCADE")
    source: str
    averaging: str  # hour | day
    value: float
    unit: str
    note: Optional[str] = Field(default=None)


class DatasetParameter(SQLModel, table=True):
    """Per dataset and parameter summary, derived from `measurement` at load."""

    __tablename__ = "dataset_parameter"

    dataset_id: int = Field(
        primary_key=True, foreign_key="dataset.id", ondelete="CASCADE"
    )
    parameter: str = Field(
        primary_key=True, foreign_key="parameter.slug", ondelete="CASCADE"
    )
    unit: str
    n_records: int = Field(sa_column=Column(BigInteger, nullable=False))
    n_missing: int = Field(sa_column=Column(BigInteger, nullable=False))
    first_at: datetime = Field(sa_column=Column(TIMESTAMP, nullable=False))
    last_at: datetime = Field(sa_column=Column(TIMESTAMP, nullable=False))
    n_buildings: int
    n_spaces: int


class CatalogVersion(SQLModel, table=True):
    """Single row bumped by publish, delete and seed; keys every cache entry."""

    __tablename__ = "catalog_version"

    id: int = Field(primary_key=True)
    version: int


measurement = Table(
    "measurement",
    SQLModel.metadata,
    Column(
        "dataset_id",
        Integer,
        ForeignKey("dataset.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "study_id", Integer, ForeignKey("study.id", ondelete="CASCADE"), nullable=False
    ),
    Column("building_id", Integer, ForeignKey("building.id", ondelete="CASCADE")),
    Column("space_id", Integer, ForeignKey("space.id", ondelete="CASCADE")),
    Column("instrument_id", Integer, ForeignKey("instrument.id", ondelete="CASCADE")),
    Column(
        "parameter",
        String,
        ForeignKey("parameter.slug", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("data_type", String, nullable=False),
    # local wall-clock time, as the CSV contains it
    Column("ts", TIMESTAMP, nullable=False),
    Column("start_ts", TIMESTAMP),
    Column("end_ts", TIMESTAMP),
    Column("value", Float, nullable=False),
    Column("value_qualifier", String),
    Index("ix_measurement_parameter_ts", "parameter", "ts"),
    Index("ix_measurement_dataset_parameter_ts", "dataset_id", "parameter", "ts"),
    Index("ix_measurement_space_ts", "space_id", "ts"),
    # every cascading FK needs an index on its column: deleting a catalog row
    # runs `DELETE FROM measurement WHERE <fk> = $1`, and without one that is
    # a scan of the whole hypertable per deleted building, space, instrument
    Index("ix_measurement_building_id", "building_id"),
    Index("ix_measurement_instrument_id", "instrument_id"),
    Index("ix_measurement_study_id", "study_id"),
)

# Columns copied in, in this order (see MeasurementService.load)
MEASUREMENT_COLUMNS = [
    "dataset_id",
    "study_id",
    "building_id",
    "space_id",
    "instrument_id",
    "parameter",
    "data_type",
    "ts",
    "start_ts",
    "end_ts",
    "value",
    "value_qualifier",
]

# Indexes dropped for the bulk seed and rebuilt after it: only the query
# index whose leading column is not a foreign key. The FK-leading indexes stay
# so that recreating a study (the seed deletes and re-inserts its catalog rows)
# keeps every cascade an index lookup instead of a scan of the hypertable.
MEASUREMENT_BULK_INDEXES = {"ix_measurement_parameter_ts": "parameter, ts"}


class LoadReport(BaseModel):
    """Where every row of a dataset's files went. Stored on the dataset and
    printed by the seed, so a rejected row is never silent."""

    loaded: int = 0
    missing: int = 0
    statistical: int = 0
    unknown_parameter: Dict[str, int] = {}
    unknown_unit: Dict[str, int] = {}
    unparseable_value: Dict[str, int] = {}
    unparseable_timestamp: int = 0
    unlinked_building: int = 0
    unlinked_space: int = 0
    unlinked_instrument: int = 0

    @property
    def rejected(self) -> int:
        return (
            sum(self.unknown_parameter.values())
            + sum(self.unknown_unit.values())
            + sum(self.unparseable_value.values())
            + self.unparseable_timestamp
        )

    def summary(self) -> str:
        parts = [f"loaded {self.loaded}"]
        if self.missing:
            parts.append(f"missing {self.missing}")
        if self.statistical:
            parts.append(f"statistical {self.statistical}")
        if self.unknown_parameter:
            parts.append(
                f"unknown parameter {sum(self.unknown_parameter.values())} "
                f"({len(self.unknown_parameter)} slugs)"
            )
        if self.unknown_unit:
            parts.append(
                f"unknown unit {sum(self.unknown_unit.values())} "
                f"({', '.join(sorted(self.unknown_unit))})"
            )
        if self.unparseable_value:
            parts.append(f"unparseable value {sum(self.unparseable_value.values())}")
        if self.unparseable_timestamp:
            parts.append(f"unparseable timestamp {self.unparseable_timestamp}")
        unlinked = [
            f"{name} {n}"
            for name, n in (
                ("building", self.unlinked_building),
                ("space", self.unlinked_space),
                ("instrument", self.unlinked_instrument),
            )
            if n
        ]
        if unlinked:
            parts.append("unlinked " + ", ".join(unlinked))
        return ", ".join(parts)
