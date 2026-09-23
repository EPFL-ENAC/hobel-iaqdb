import pytest
from api.models.catalog import Dataset
from api.models.measurement import DatasetParameter
from api.services.measurement import MeasurementService
from sqlalchemy import text
from sqlmodel import select
from tests.fixtures import CSV_COLUMNS, D1_REPORT, daily, hourly, make_fixture, mean


async def load_all(session, engine, tmp_path):
    fx = await make_fixture(session, tmp_path)
    service = MeasurementService(engine)
    reports = {
        name: await service.load(fx.datasets[name], paths)
        for name, paths in fx.files.items()
    }
    return fx, reports


async def test_report_bins(session, clean_db, tmp_path):
    fx, reports = await load_all(session, clean_db, tmp_path)
    report = reports["D1"]
    expected_loaded = sum(
        len(v) for (slug, space), v in fx.series.items() if slug != "pm2_5"
    )
    assert report.loaded == expected_loaded
    assert report.model_dump(exclude={"loaded"}) == D1_REPORT
    assert reports["D2"].loaded == len(fx.series[("pm2_5", "S3")])
    assert reports["D2"].rejected == 0
    dataset = await session.get(Dataset, fx.datasets["D1"])
    await session.refresh(dataset)
    assert dataset.summary_status == "ready"
    assert dataset.load_report["unlinked_space"] == 1


async def test_rows_and_units(session, clean_db, tmp_path):
    fx, _ = await load_all(session, clean_db, tmp_path)
    rows = (
        await session.exec(
            text(
                "SELECT space_id, parameter, ts, value, data_type, start_ts, end_ts"
                " FROM measurement WHERE dataset_id = :id ORDER BY ts"
            ).bindparams(id=fx.datasets["D2"])
        )
    ).all()
    assert len(rows) == len(fx.series[("pm2_5", "S3")])
    integrated = rows[-1]
    assert integrated.data_type == "time_integrated"
    assert integrated.value == pytest.approx(12.0)  # mg/m³ -> µg/m³
    assert integrated.ts == integrated.start_ts
    assert integrated.end_ts is not None
    assert all(r.space_id == fx.spaces["S3"] for r in rows)
    # decimal comma, tz offset and unknown space rows of D1
    tail = (
        await session.exec(
            text(
                "SELECT space_id, parameter, value FROM measurement"
                " WHERE dataset_id = :id AND ts = '2023-03-07 01:00' ORDER BY value"
            ).bindparams(id=fx.datasets["D1"])
        )
    ).all()
    assert [(r.parameter, r.value) for r in tail] == [
        ("air_temperature", 21.5),
        ("co2", 500.0),
        ("co2", 510.0),
    ]
    assert tail[2].space_id is None


async def test_dataset_parameter_summary(session, clean_db, tmp_path):
    fx, _ = await load_all(session, clean_db, tmp_path)
    rows = (
        await session.exec(
            select(DatasetParameter).where(
                DatasetParameter.dataset_id == fx.datasets["D1"]
            )
        )
    ).all()
    by_slug = {r.parameter: r for r in rows}
    assert set(by_slug) == {"co2", "air_temperature"}
    co2 = by_slug["co2"]
    assert co2.n_records == sum(
        len(v) for (slug, _), v in fx.series.items() if slug == "co2"
    )
    assert co2.n_missing == 2
    assert co2.unit == "ppm"
    assert co2.n_buildings == 1 and co2.n_spaces == 2  # S9 is unlinked
    assert co2.first_at == fx.series[("co2", "S1")][0][0]
    assert co2.last_at == fx.series[("co2", "S1")][-1][0]


async def test_continuous_aggregates_match_raw(session, clean_db, tmp_path):
    fx, _ = await load_all(session, clean_db, tmp_path)
    for (slug, space), points in fx.series.items():
        if space == "S9":
            continue
        hours = (
            await session.exec(
                text(
                    "SELECT hour, n, mean, min, max FROM measurement_hour"
                    " WHERE parameter = :slug AND space_id = :space ORDER BY hour"
                ).bindparams(slug=slug, space=fx.spaces[space])
            )
        ).all()
        expected = hourly(points)
        assert [h.hour for h in hours] == sorted(expected)
        for h in hours:
            values = expected[h.hour]
            assert h.n == len(values)
            assert h.mean == pytest.approx(mean(values))
            assert (h.min, h.max) == (min(values), max(values))
        days = (
            await session.exec(
                text(
                    "SELECT day, n, mean FROM measurement_day"
                    " WHERE parameter = :slug AND space_id = :space ORDER BY day"
                ).bindparams(slug=slug, space=fx.spaces[space])
            )
        ).all()
        expected_days = daily(points)
        assert [d.day for d in days] == sorted(expected_days)
        for d in days:
            assert d.n == len(expected_days[d.day])
            assert d.mean == pytest.approx(mean(expected_days[d.day]))


async def test_statistical_rows_are_not_aggregated(session, clean_db, tmp_path):
    fx, reports = await load_all(session, clean_db, tmp_path)
    assert reports["D1"].statistical == 1
    n = (
        await session.exec(
            text("SELECT count(*) FROM measurement WHERE data_type = 'statistical'")
        )
    ).scalar()
    assert n == 0


async def test_reload_is_idempotent_and_delete_cascades(session, clean_db, tmp_path):
    fx, _ = await load_all(session, clean_db, tmp_path)
    service = MeasurementService(clean_db)
    before = (await session.exec(text("SELECT count(*) FROM measurement"))).scalar()
    await service.load(fx.datasets["D1"], fx.files["D1"])
    after = (await session.exec(text("SELECT count(*) FROM measurement"))).scalar()
    assert before == after
    hours_before = (
        await session.exec(text("SELECT count(*) FROM measurement_hour"))
    ).scalar()
    dataset = await session.get(Dataset, fx.datasets["D2"])
    await session.delete(dataset)
    await session.commit()
    await service.refresh_all()
    left = (
        await session.exec(text("SELECT count(DISTINCT dataset_id) FROM measurement"))
    ).scalar()
    assert left == 1
    hours_after = (
        await session.exec(text("SELECT count(*) FROM measurement_hour"))
    ).scalar()
    assert hours_after == hours_before - len(hourly(fx.series[("pm2_5", "S3")]))
    summaries = (
        await session.exec(text("SELECT count(*) FROM dataset_parameter"))
    ).scalar()
    assert summaries == 2


async def test_compression_and_empty_file(session, clean_db, tmp_path):
    fx, _ = await load_all(session, clean_db, tmp_path)
    service = MeasurementService(clean_db)
    chunks = (
        await session.exec(
            text(
                "SELECT count(*) FROM timescaledb_information.chunks"
                " WHERE hypertable_name = 'measurement' AND is_compressed"
            )
        )
    ).scalar()
    assert chunks >= 1
    partial = tmp_path / "partial.csv"
    partial.write_text(",".join(["dataset_id", "parameter", "value"]) + "\n")
    with pytest.raises(ValueError, match="missing columns"):
        await service.load(fx.datasets["D2"], [partial])
    dataset = await session.get(Dataset, fx.datasets["D2"])
    await session.refresh(dataset)
    assert dataset.summary_status == "failed"
    assert "missing columns" in dataset.summary_error
    empty = tmp_path / "empty.csv"
    empty.write_text(",".join(CSV_COLUMNS) + "\n")
    with pytest.raises(ValueError, match="no row loaded"):
        await service.load(fx.datasets["D2"], [empty])
    dataset = await session.get(Dataset, fx.datasets["D2"])
    await session.refresh(dataset)
    assert dataset.summary_status == "failed"
    assert dataset.summary_error == "no row loaded"
    n = (
        await session.exec(
            text("SELECT count(*) FROM measurement WHERE dataset_id = :id").bindparams(
                id=dataset.id
            )
        )
    ).scalar()
    assert n == 0
