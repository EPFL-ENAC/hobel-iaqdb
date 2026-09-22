"""One study with a known answer.

Two buildings (CH office, DE school), three spaces, two datasets:
- D1: co2 and air_temperature, 10-minute readings over 6 days in spaces S1 and
  S2, plus one row per rejection bin.
- D2: pm2_5 hourly in S3 over 6 days, one time_integrated row.
Values are deterministic functions of time so tests recompute them.
"""

import csv
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from api.models.catalog import (
    Building,
    Dataset,
    Instrument,
    Space,
    Study,
)
from sqlmodel.ext.asyncio.session import AsyncSession

START = datetime(2023, 3, 1, 0, 0)
DAYS = 6
CSV_COLUMNS = [
    "project_id",
    "project_name",
    "dataset_id",
    "data_type",
    "source_outer_file",
    "source_logical_file",
    "source_row",
    "source_column",
    "record_id",
    "source_building_id",
    "building_id",
    "source_space_id",
    "space_id",
    "source_instrument_id",
    "instrument_id",
    "timestamp",
    "start_timestamp",
    "end_timestamp",
    "measurement_period",
    "elapsed_time",
    "parameter",
    "statistic",
    "value",
    "real_unit",
    "inferred_unit",
    "value_qualifier",
    "context_json",
]


def co2_at(t: datetime, space: str) -> float:
    hours = (t - START).total_seconds() / 3600
    base = 420 if space == "S1" else 480
    return round(base + 250 * (1 + math.sin(hours / 24 * 2 * math.pi)), 3)


def temperature_at(t: datetime, space: str) -> float:
    hours = (t - START).total_seconds() / 3600
    return round(20 + (1 if space == "S1" else 2) * math.cos(hours / 6), 3)


def pm25_at(t: datetime) -> float:
    hours = (t - START).total_seconds() / 3600
    return round(5 + (hours % 48) / 4, 3)


@dataclass
class Row:
    dataset: str
    building: str
    space: str
    parameter: str
    value: str
    unit: str = ""
    inferred_unit: str = ""
    timestamp: str = ""
    start: str = ""
    end: str = ""
    data_type: str = "time_series"
    instrument: str = "I1"
    statistic: str = ""
    qualifier: str = ""

    def as_csv(self) -> dict:
        return {
            "dataset_id": self.dataset,
            "data_type": self.data_type,
            "building_id": self.building,
            "space_id": self.space,
            "instrument_id": self.instrument,
            "timestamp": self.timestamp,
            "start_timestamp": self.start,
            "end_timestamp": self.end,
            "parameter": self.parameter,
            "statistic": self.statistic,
            "value": self.value,
            "real_unit": self.unit,
            "inferred_unit": self.inferred_unit,
            "value_qualifier": self.qualifier,
        }


@dataclass
class Fixture:
    study_id: int
    buildings: dict[str, int]
    spaces: dict[str, int]
    datasets: dict[str, int]
    files: dict[str, list[Path]]
    # (slug, space) -> [(ts, canonical value)] of rows expected to load
    series: dict[tuple[str, str], list[tuple[datetime, float]]] = field(
        default_factory=dict
    )


def series_rows(
    dataset: str, building: str, space: str, slug: str, unit: str, step: timedelta, fn
) -> tuple[list[Row], list[tuple[datetime, float]]]:
    rows, expected = [], []
    t = START
    while t < START + timedelta(days=DAYS):
        value = fn(t)
        rows.append(
            Row(dataset, building, space, slug, str(value), unit, timestamp=t.isoformat())
        )
        expected.append((t, value))
        t += step
    return rows, expected


def d1_rows(fx: Fixture) -> list[Row]:
    rows = []
    for space in ("S1", "S2"):
        co2, exp = series_rows(
            "D1", "B1", space, "co2", "ppm", timedelta(minutes=10),
            lambda t, s=space: co2_at(t, s),
        )
        fx.series[("co2", space)] = exp
        temp, exp = series_rows(
            "D1", "B1", space, "air_temperature", "°C", timedelta(minutes=10),
            lambda t, s=space: temperature_at(t, s),
        )
        fx.series[("air_temperature", space)] = exp
        rows += co2 + temp
    ts = (START + timedelta(days=DAYS, hours=1)).isoformat()
    rows += [
        # accepted through the inferred unit, value with a decimal comma
        Row("D1", "B1", "S1", "air_temperature", "21,5", "", "°C", ts),
        # wall clock kept, offset dropped
        Row("D1", "B1", "S1", "co2", "500", "ppm", timestamp=ts + "+02:00"),
        # unknown space: loaded, unlinked
        Row("D1", "B1", "S9", "co2", "510", "ppm", timestamp=ts),
        # rejected bins
        Row("D1", "B1", "S1", "occupancy", "Day 1", "", "not applicable", ts),
        Row("D1", "B1", "S1", "co2", "0.9", "mg/m³", timestamp=ts),
        Row("D1", "B1", "S1", "co2", "NA", "ppm", timestamp=ts),
        Row("D1", "B1", "S1", "co2", "", "ppm", timestamp=ts),
        Row("D1", "B1", "S1", "co2", "1.5 K", "ppm", timestamp=ts),
        Row("D1", "B1", "S1", "co2", "520", "ppm", timestamp="NA"),
        Row("D1", "B1", "S1", "co2", "530", "ppm", timestamp="2023-03"),
        Row("D1", "B1", "S1", "co2", "700", "ppm", data_type="statistical", statistic="p95"),
    ]
    fx.series[("air_temperature", "S1")].append((START + timedelta(days=DAYS, hours=1), 21.5))
    fx.series[("co2", "S1")].append((START + timedelta(days=DAYS, hours=1), 500.0))
    fx.series[("co2", "S9")] = [(START + timedelta(days=DAYS, hours=1), 510.0)]
    return rows


D1_REPORT = {
    "missing": 2,
    "statistical": 1,
    "unknown_parameter": {"occupancy": 1},
    "unknown_unit": {"co2|mg/m³": 1},
    "unparseable_value": {"co2": 1},
    "unparseable_timestamp": 2,
    "unlinked_building": 0,
    "unlinked_space": 1,
    "unlinked_instrument": 0,
}


def d2_rows(fx: Fixture) -> list[Row]:
    rows, exp = series_rows(
        "D2", "B2", "S3", "pm2_5", "µg/m³", timedelta(hours=1), pm25_at
    )
    fx.series[("pm2_5", "S3")] = exp
    # 24-h gravimetric sample in mg/m³: ts = start, value converted
    start = START + timedelta(days=DAYS)
    rows.append(
        Row(
            "D2", "B2", "S3", "pm2_5", "0.012", "mg/m³",
            start=start.isoformat(), end=(start + timedelta(days=1)).isoformat(),
            data_type="time_integrated", instrument="I2",
        )
    )
    fx.series[("pm2_5", "S3")].append((start, 12.0))
    return rows


def write_csv(path: Path, rows: list[Row]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({**{c: "" for c in CSV_COLUMNS}, **row.as_csv()})
    return path


async def make_catalog(session: AsyncSession) -> Fixture:
    study = Study(identifier="study-a", name="Study A")
    session.add(study)
    await session.commit()
    b1 = Building(
        identifier="B1", country="CH", city="Zurich", type="office",
        climate_zone="Cfb", mechanical_ventilation="yes", construction_year=1990,
        altitude=400, study_id=study.id,
    )
    b2 = Building(
        identifier="B2", country="DE", city="Berlin", type="school",
        climate_zone="Dfb", mechanical_ventilation="no", study_id=study.id,
    )
    session.add_all([b1, b2])
    await session.commit()
    spaces = [
        Space(identifier="S1", type="office", mechanical_ventilation_type="mechanical",
              occupancy="occupied", occupancy_density=0.1, floor_area=40.0,
              study_id=study.id, building_id=b1.id),
        Space(identifier="S2", type="meeting room", mechanical_ventilation_type="natural",
              occupancy="occupied", occupancy_density=0.3, study_id=study.id,
              building_id=b1.id),
        Space(identifier="S3", type="classroom", mechanical_ventilation_type="natural",
              occupancy="occupied", study_id=study.id, building_id=b2.id),
    ]
    session.add_all(spaces)
    session.add_all(
        [
            Instrument(identifier="I1", study_id=study.id),
            Instrument(identifier="I2", study_id=study.id),
        ]
    )
    datasets = [
        Dataset(name="D1", description="co2 and temperature", study_id=study.id),
        Dataset(name="D2", description="pm2.5", study_id=study.id),
    ]
    session.add_all(datasets)
    await session.commit()
    return Fixture(
        study_id=study.id,
        buildings={"B1": b1.id, "B2": b2.id},
        spaces={s.identifier: s.id for s in spaces},
        datasets={d.name: d.id for d in datasets},
        files={},
    )


async def make_fixture(session: AsyncSession, tmp_path: Path) -> Fixture:
    fx = await make_catalog(session)
    fx.files["D1"] = [write_csv(tmp_path / "d1_long.csv", d1_rows(fx))]
    fx.files["D2"] = [write_csv(tmp_path / "d2_long.csv", d2_rows(fx))]
    return fx


def hourly(points: list[tuple[datetime, float]]) -> dict[datetime, list[float]]:
    buckets: dict[datetime, list[float]] = {}
    for t, v in points:
        buckets.setdefault(t.replace(minute=0, second=0, microsecond=0), []).append(v)
    return buckets


def daily(points: list[tuple[datetime, float]]) -> dict[datetime, list[float]]:
    buckets: dict[datetime, list[float]] = {}
    for t, v in points:
        buckets.setdefault(t.replace(hour=0, minute=0, second=0), []).append(v)
    return buckets


def mean(values: list[float]) -> float:
    return sum(values) / len(values)
