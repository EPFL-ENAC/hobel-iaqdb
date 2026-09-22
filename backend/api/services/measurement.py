"""Load processed long-format CSVs into the `measurement` hypertable.

Every row of every file goes to exactly one bin of the LoadReport: loaded,
missing, statistical, unknown parameter/unit, unparseable value/timestamp.
Nothing is guessed: a rejected row is counted and reported, never fixed.

The CSV side is DuckDB (streaming, bounded memory); the database side is
asyncpg COPY, then compression, continuous aggregate refresh and the
`dataset_parameter` summary. `refresh_all` only recomputes the buckets that
TimescaleDB marked invalid, so it is the one refresh every load and delete
path calls (design §3, updated).
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import duckdb
from api.models.catalog import Building, Dataset, Instrument, Space
from api.models.measurement import (
    MEASUREMENT_BULK_INDEXES,
    MEASUREMENT_COLUMNS,
    DatasetParameter,
    LoadReport,
    Parameter,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import col, delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

BATCH_SIZE = 50_000
REQUIRED_COLUMNS = (
    "data_type",
    "building_id",
    "space_id",
    "instrument_id",
    "timestamp",
    "start_timestamp",
    "end_timestamp",
    "parameter",
    "value",
    "real_unit",
    "inferred_unit",
    "value_qualifier",
)
MISSING_VALUES = ("", "NA", "N/A", "NAN", "NULL", "NONE")
# units the processed CSVs use to say "no unit"
NO_UNIT = ("", "not applicable", "unknown")
# trailing UTC offset or Z after a time of day: dropped, the wall clock is kept
TZ_SUFFIX = r"(\d{2}:\d{2}(:\d{2}(\.\d+)?)?)(Z|[+-]\d{2}:?\d{2})$"
DECIMAL_COMMA = r"^-?\d+,\d+$"
BINS = (
    "statistical",
    "unknown_parameter",
    "unknown_unit",
    "missing",
    "unparseable_value",
    "unparseable_timestamp",
    "loaded",
)


@dataclass
class CatalogMaps:
    """Identifier -> id of the study's catalog entities, for the CSV columns
    `building_id`, `space_id` (unique within a building), `instrument_id`."""

    buildings: dict[str, int] = field(default_factory=dict)
    spaces: dict[tuple[str, str], int] = field(default_factory=dict)
    instruments: dict[str, int] = field(default_factory=dict)


@dataclass
class Classification:
    report: LoadReport
    # per parameter slug: rows with a missing value (feeds n_missing)
    missing: dict[str, int]
    first_at: object = None
    last_at: object = None


def _files_sql(files: list[str]) -> str:
    return "[" + ", ".join("'" + f.replace("'", "''") + "'" for f in files) + "]"


def _classified_sql(files: list[str]) -> str:
    files_sql = _files_sql(files)
    missing_sql = ", ".join(f"'{v}'" for v in MISSING_VALUES)
    no_unit_sql = ", ".join(f"'{v}'" for v in NO_UNIT)
    return f"""
    WITH raw AS (
        SELECT
            coalesce(trim(parameter), '') AS slug,
            coalesce(trim(data_type), '') AS data_type,
            nullif(trim(building_id), '') AS building_ident,
            nullif(trim(space_id), '') AS space_ident,
            nullif(trim(instrument_id), '') AS instrument_ident,
            nullif(trim("timestamp"), '') AS timestamp_text,
            nullif(trim(start_timestamp), '') AS start_text,
            nullif(trim(end_timestamp), '') AS end_text,
            coalesce(trim(value), '') AS value_text,
            nullif(trim(value_qualifier), '') AS value_qualifier,
            coalesce(
                nullif(trim(real_unit), ''),
                CASE WHEN lower(coalesce(trim(inferred_unit), '')) IN ({no_unit_sql})
                     THEN NULL ELSE trim(inferred_unit) END
            ) AS unit
        FROM read_csv({files_sql}, header = true, all_varchar = true,
                      union_by_name = true)
    ),
    typed AS (
        SELECT r.*, d.factor, d.off, d.unit AS accepted_unit, k.slug AS known_slug,
            b.id AS building_id, s.id AS space_id, i.id AS instrument_id,
            CASE WHEN upper(value_text) IN ({missing_sql}) THEN NULL
                 WHEN regexp_matches(value_text, '{DECIMAL_COMMA}')
                 THEN try_cast(replace(value_text, ',', '.') AS DOUBLE)
                 ELSE try_cast(value_text AS DOUBLE) END AS value,
            try_cast(regexp_replace(
                CASE WHEN data_type = 'time_integrated'
                     THEN coalesce(start_text, timestamp_text)
                     ELSE timestamp_text END, '{TZ_SUFFIX}', '\\1') AS TIMESTAMP) AS ts,
            try_cast(regexp_replace(start_text, '{TZ_SUFFIX}', '\\1') AS TIMESTAMP)
                AS start_ts,
            try_cast(regexp_replace(end_text, '{TZ_SUFFIX}', '\\1') AS TIMESTAMP)
                AS end_ts
        FROM raw r
        LEFT JOIN (SELECT DISTINCT slug FROM dictionary) k ON k.slug = r.slug
        LEFT JOIN dictionary d ON d.slug = r.slug AND d.unit = r.unit
        LEFT JOIN buildings b ON b.identifier = r.building_ident
        LEFT JOIN spaces s ON s.building = r.building_ident
                          AND s.identifier = r.space_ident
        LEFT JOIN instruments i ON i.identifier = r.instrument_ident
    ),
    classified AS (
        SELECT *,
            CASE WHEN data_type = 'statistical' THEN 'statistical'
                 WHEN known_slug IS NULL THEN 'unknown_parameter'
                 WHEN accepted_unit IS NULL THEN 'unknown_unit'
                 WHEN upper(value_text) IN ({missing_sql}) THEN 'missing'
                 WHEN value IS NULL OR isnan(value) OR isinf(value)
                 THEN 'unparseable_value'
                 WHEN ts IS NULL THEN 'unparseable_timestamp'
                 ELSE 'loaded' END AS bin
        FROM typed
    )
    """


class MeasurementReader:
    """DuckDB view of a dataset's files, classified against the dictionary
    and the study's catalog. Blocking: call it from a thread."""

    def __init__(
        self, paths: list[Path], parameters: list[Parameter], maps: CatalogMaps
    ):
        self.files = [str(p) for p in paths]
        self.con = duckdb.connect()
        self._check_columns()
        self._register(parameters, maps)

    def _check_columns(self) -> None:
        files_sql = _files_sql(self.files)
        rows = self.con.execute(
            f"DESCRIBE SELECT * FROM read_csv({files_sql}, header = true,"
            " all_varchar = true, union_by_name = true)"
        ).fetchall()
        missing = sorted(set(REQUIRED_COLUMNS) - {r[0] for r in rows})
        if missing:
            raise ValueError(f"missing columns {missing} in {self.files}")

    def _register(self, parameters: list[Parameter], maps: CatalogMaps) -> None:
        con = self.con
        con.execute("CREATE TABLE dictionary (slug VARCHAR, unit VARCHAR, factor DOUBLE, off DOUBLE)")
        con.executemany(
            "INSERT INTO dictionary VALUES (?, ?, ?, ?)",
            [
                (p.slug, unit, conv["factor"], conv.get("offset", 0.0))
                for p in parameters
                for unit, conv in p.conversions.items()
            ],
        )
        con.execute("CREATE TABLE buildings (identifier VARCHAR, id INTEGER)")
        con.executemany(
            "INSERT INTO buildings VALUES (?, ?)", list(maps.buildings.items())
        )
        con.execute("CREATE TABLE spaces (building VARCHAR, identifier VARCHAR, id INTEGER)")
        con.executemany(
            "INSERT INTO spaces VALUES (?, ?, ?)",
            [(b, s, i) for (b, s), i in maps.spaces.items()],
        )
        con.execute("CREATE TABLE instruments (identifier VARCHAR, id INTEGER)")
        con.executemany(
            "INSERT INTO instruments VALUES (?, ?)", list(maps.instruments.items())
        )

    def classify(self) -> Classification:
        rows = self.con.execute(
            _classified_sql(self.files)
            + """
            SELECT bin, slug, unit, count(*),
                   count(*) FILTER (WHERE bin = 'loaded' AND building_id IS NULL),
                   count(*) FILTER (WHERE bin = 'loaded' AND space_id IS NULL),
                   count(*) FILTER (WHERE bin = 'loaded' AND instrument_id IS NULL),
                   min(ts) FILTER (WHERE bin = 'loaded'),
                   max(ts) FILTER (WHERE bin = 'loaded')
            FROM classified GROUP BY 1, 2, 3
            """
        ).fetchall()
        return _summarize(rows)

    def loaded(self, dataset_id: int, study_id: int) -> Iterator[list[tuple]]:
        """Batches of `measurement` rows (MEASUREMENT_COLUMNS order),
        values converted to the canonical unit."""
        cursor = self.con.execute(
            _classified_sql(self.files)
            + f"""
            SELECT {dataset_id}, {study_id}, building_id, space_id, instrument_id,
                   slug, data_type, ts, start_ts, end_ts,
                   value * factor + off, value_qualifier
            FROM classified WHERE bin = 'loaded'
            """
        )
        while True:
            batch = cursor.fetchmany(BATCH_SIZE)
            if not batch:
                return
            yield batch

    def close(self) -> None:
        self.con.close()


def _summarize(rows: list[tuple]) -> Classification:
    report = LoadReport()
    missing: dict[str, int] = {}
    first_at = last_at = None
    for bin_, slug, unit, n, no_building, no_space, no_instrument, lo, hi in rows:
        if bin_ == "loaded":
            report.loaded += n
            report.unlinked_building += no_building
            report.unlinked_space += no_space
            report.unlinked_instrument += no_instrument
            first_at = lo if first_at is None else min(first_at, lo)
            last_at = hi if last_at is None else max(last_at, hi)
        elif bin_ == "missing":
            report.missing += n
            missing[slug] = missing.get(slug, 0) + n
        elif bin_ == "statistical":
            report.statistical += n
        elif bin_ == "unparseable_timestamp":
            report.unparseable_timestamp += n
        elif bin_ == "unknown_unit":
            key = f"{slug}|{unit or ''}"
            report.unknown_unit[key] = report.unknown_unit.get(key, 0) + n
        else:
            counter = getattr(report, bin_)
            counter[slug] = counter.get(slug, 0) + n
    return Classification(report, missing, first_at, last_at)


class MeasurementService:
    """Owns the measurement side of a dataset: load, refresh, compress."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def load(
        self, dataset_id: int, paths: list[Path], bulk: bool = False
    ) -> LoadReport:
        """Replace the dataset's measurements with the content of `paths`.
        Idempotent. Marks the dataset ready or failed; a failure is raised.
        `bulk` (seed) skips compression and the aggregate refresh and turns
        synchronous commits off: the seed does them once at the end."""
        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            dataset = await session.get(Dataset, dataset_id)
            if dataset is None:
                raise ValueError(f"dataset {dataset_id} not found")
            parameters = list((await session.exec(select(Parameter))).all())
            maps = await self._catalog_maps(session, dataset.study_id)
            await self._begin(session, dataset)
        try:
            classification = await self._copy(dataset, paths, parameters, maps, bulk)
        except Exception as e:
            await self.fail(dataset_id, f"{type(e).__name__}: {e}")
            raise
        report = classification.report
        if report.loaded == 0:
            await self._finish(dataset_id, report, "failed", "no row loaded")
            raise ValueError(f"no row loaded: {report.summary()}")
        await self._finish(dataset_id, report, "ready", None)
        return report

    async def fail(self, dataset_id: int, error: str) -> None:
        """Record a failure that happened before or outside `load`."""
        await self._finish(dataset_id, None, "failed", error)

    async def _catalog_maps(self, session: AsyncSession, study_id: int) -> CatalogMaps:
        maps = CatalogMaps()
        buildings = (
            await session.exec(select(Building).where(Building.study_id == study_id))
        ).all()
        by_id = {b.id: b.identifier for b in buildings}
        maps.buildings = {b.identifier: b.id for b in buildings}
        spaces = (
            await session.exec(select(Space).where(Space.study_id == study_id))
        ).all()
        maps.spaces = {
            (by_id[s.building_id], s.identifier): s.id
            for s in spaces
            if s.building_id in by_id
        }
        instruments = (
            await session.exec(
                select(Instrument).where(Instrument.study_id == study_id)
            )
        ).all()
        maps.instruments = {i.identifier: i.id for i in instruments}
        return maps

    async def _begin(self, session: AsyncSession, dataset: Dataset) -> None:
        dataset.summary_status = "pending"
        dataset.summary_error = None
        dataset.load_report = None
        session.add(dataset)
        await session.exec(
            delete(DatasetParameter).where(
                col(DatasetParameter.dataset_id) == dataset.id
            )
        )
        await session.exec(
            text("DELETE FROM measurement WHERE dataset_id = :id").bindparams(
                id=dataset.id
            )
        )
        await session.commit()

    async def _copy(
        self,
        dataset: Dataset,
        paths: list[Path],
        parameters: list[Parameter],
        maps: CatalogMaps,
        bulk: bool,
    ) -> Classification:
        reader = await asyncio.to_thread(MeasurementReader, paths, parameters, maps)
        try:
            classification = await asyncio.to_thread(reader.classify)
            if classification.report.loaded:
                await self._copy_batches(reader, dataset, bulk)
        finally:
            reader.close()
        if not classification.report.loaded:
            return classification
        if not bulk:
            await self.refresh_all()
            await self.compress(classification.first_at, classification.last_at)
        await self._summarize(dataset.id, classification.missing)
        return classification

    async def _copy_batches(
        self, reader: MeasurementReader, dataset: Dataset, bulk: bool
    ) -> None:
        batches = reader.loaded(dataset.id, dataset.study_id)
        async with self.engine.connect() as conn:
            raw = await conn.get_raw_connection()
            pg = raw.driver_connection
            if bulk:
                await pg.execute("SET synchronous_commit = off")
            while True:
                batch = await asyncio.to_thread(next, batches, None)
                if batch is None:
                    break
                await pg.copy_records_to_table(
                    "measurement", records=batch, columns=MEASUREMENT_COLUMNS
                )

    async def _summarize(self, dataset_id: int, missing: dict[str, int]) -> None:
        """Derive `dataset_parameter` from the loaded rows, in one statement."""
        async with AsyncSession(self.engine) as session:
            await session.exec(
                text(
                    """
                    INSERT INTO dataset_parameter
                        (dataset_id, parameter, unit, n_records, n_missing,
                         first_at, last_at, n_buildings, n_spaces)
                    SELECT m.dataset_id, m.parameter, p.unit, count(*), 0,
                           min(m.ts), max(m.ts),
                           count(DISTINCT m.building_id), count(DISTINCT m.space_id)
                    FROM measurement m JOIN parameter p ON p.slug = m.parameter
                    WHERE m.dataset_id = :id
                    GROUP BY m.dataset_id, m.parameter, p.unit
                    """
                ).bindparams(id=dataset_id)
            )
            for slug, n in missing.items():
                await session.exec(
                    text(
                        "UPDATE dataset_parameter SET n_missing = :n"
                        " WHERE dataset_id = :id AND parameter = :slug"
                    ).bindparams(n=n, id=dataset_id, slug=slug)
                )
            await session.commit()

    async def _finish(
        self, dataset_id: int, report: LoadReport | None, status: str, error: str | None
    ) -> None:
        async with AsyncSession(self.engine) as session:
            dataset = await session.get(Dataset, dataset_id)
            dataset.summary_status = status
            dataset.summary_error = error
            dataset.load_report = report.model_dump() if report else None
            session.add(dataset)
            await session.commit()

    async def refresh_all(self) -> None:
        """Bring both continuous aggregates up to date with `measurement`.
        Only invalidated buckets are recomputed. Runs outside a transaction,
        as TimescaleDB requires."""
        async with self.engine.connect() as conn:
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            for view in ("measurement_hour", "measurement_day"):
                await conn.execute(
                    text(f"CALL refresh_continuous_aggregate('{view}', NULL, NULL)")
                )

    async def compress(self, first_at, last_at) -> int:
        """Compress (or recompress) every chunk overlapping [first_at, last_at].
        Returns the number of chunks."""
        async with self.engine.connect() as conn:
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            result = await conn.execute(
                text(
                    """
                    SELECT count(compress_chunk(c, if_not_compressed => true))
                    FROM show_chunks('measurement',
                        older_than => CAST(:last AS TIMESTAMP) + INTERVAL '2 month',
                        newer_than => CAST(:first AS TIMESTAMP) - INTERVAL '2 month') c
                    """
                ).bindparams(first=first_at, last=last_at)
            )
            return result.scalar_one()

    async def compress_all(self) -> int:
        async with self.engine.connect() as conn:
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            result = await conn.execute(
                text(
                    "SELECT count(compress_chunk(c, if_not_compressed => true))"
                    " FROM show_chunks('measurement') c"
                )
            )
            return result.scalar_one()

    async def drop_bulk_indexes(self) -> None:
        """Seed only: the bulk COPY is twice as fast without secondary indexes."""
        async with self.engine.begin() as conn:
            for name in MEASUREMENT_BULK_INDEXES:
                await conn.execute(text(f"DROP INDEX IF EXISTS {name}"))

    async def create_bulk_indexes(self) -> None:
        async with self.engine.begin() as conn:
            for name, columns in (
                ("ix_measurement_parameter_ts", "parameter, ts"),
                ("ix_measurement_dataset_parameter_ts", "dataset_id, parameter, ts"),
                ("ix_measurement_space_ts", "space_id, ts"),
            ):
                await conn.execute(
                    text(
                        f"CREATE INDEX IF NOT EXISTS {name} ON measurement ({columns})"
                    )
                )
