"""The continuous aggregates, as Core tables for query building only.

They live on their own MetaData so Alembic never tries to create them: the
migration owns them (they are TimescaleDB materialized views)."""

from api.models.measurement import measurement
from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
)

aggregates_metadata = MetaData()


def _aggregate(name: str, bucket: str) -> Table:
    return Table(
        name,
        aggregates_metadata,
        Column("dataset_id", Integer),
        Column("study_id", Integer),
        Column("building_id", Integer),
        Column("space_id", Integer),
        Column("instrument_id", Integer),
        Column("parameter", String),
        Column(bucket, TIMESTAMP),
        Column("n", BigInteger),
        Column("mean", Float),
        Column("min", Float),
        Column("max", Float),
    )


measurement_hour = _aggregate("measurement_hour", "hour")
measurement_day = _aggregate("measurement_day", "day")

# grain -> (table, time column name, value column name, count column or None)
GRAIN_TABLES = {
    "day": (measurement_day, "day", "mean", "n"),
    "hour": (measurement_hour, "hour", "mean", "n"),
    "raw": (measurement, "ts", "value", None),
}
