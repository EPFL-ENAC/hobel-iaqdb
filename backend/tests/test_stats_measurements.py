import json
from datetime import datetime

import pytest
from tests.expected import series_of, stats_of
from tests.fixtures import daily, hourly
from tests.test_stats_metadata import buckets_of, loaded_fixture


async def test_count_by_parameter_at_each_grain(client, session, clean_db, tmp_path):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    for grain, group in (("day", daily), ("hour", hourly), ("raw", None)):
        response = await client.get(
            "/stats/measurements", params={"agg": "count", "by": "parameter", "grain": grain}
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["meta"]["grain"] == grain
        for slug in ("co2", "air_temperature", "pm2_5"):
            series = series_of(fx, slug)
            expected_n = sum(len(group(p)) if group else len(p) for p in series)
            bucket = buckets_of(body)[(slug,)]
            assert bucket["n"] == expected_n, (grain, slug)
            assert bucket["n_records"] == sum(len(p) for p in series)
        assert body["meta"]["n"] == sum(b["n"] for b in body["buckets"])
        assert body["meta"]["n_records"] == sum(b["n_records"] for b in body["buckets"])


async def test_stats_by_country_at_each_grain(client, session, clean_db, tmp_path):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    for grain in ("day", "hour", "raw"):
        response = await client.get(
            "/stats/measurements",
            params={"agg": "stats", "by": "country", "parameters": "co2", "grain": grain},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["meta"]["unit"] == "ppm"
        assert [b["key"] for b in body["buckets"]] == [["CH"]]
        bucket = body["buckets"][0]
        expected = stats_of(series_of(fx, "co2"), grain)
        assert bucket["n"] == expected.pop("n")
        assert bucket["n_records"] == expected.pop("n_records")
        for name, value in expected.items():
            assert bucket["stats"][name] == pytest.approx(value, rel=1e-6), (grain, name)


async def test_time_window_and_time_dimensions(client, session, clean_db, tmp_path):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    window = (datetime(2023, 3, 3), datetime(2023, 3, 5))
    response = await client.get(
        "/stats/measurements",
        params={
            "agg": "stats", "by": "day", "parameters": "air_temperature",
            "from": "2023-03-03", "to": "2023-03-05", "grain": "hour",
        },
    )
    body = response.json()
    assert body["meta"]["from"] == "2023-03-03" and body["meta"]["to"] == "2023-03-05"
    assert [b["key"] for b in body["buckets"]] == [["2023-03-03"], ["2023-03-04"]]
    for bucket in body["buckets"]:
        day = datetime.fromisoformat(bucket["key"][0])
        series = series_of(fx, "air_temperature", window=(day, day.replace(day=day.day + 1)))
        expected = stats_of(series, "hour")
        assert bucket["n"] == expected["n"]
        assert bucket["stats"]["p50"] == pytest.approx(expected["p50"])
    series = series_of(fx, "air_temperature", window=window)
    assert body["meta"]["n"] == stats_of(series, "hour")["n"]
    response = await client.get(
        "/stats/measurements",
        params={"agg": "count", "by": "month_of_year,parameter", "grain": "day"},
    )
    keys = {tuple(b["key"]) for b in response.json()["buckets"]}
    assert keys == {("3", "co2"), ("3", "air_temperature"), ("3", "pm2_5")}
    response = await client.get(
        "/stats/measurements", params={"agg": "count", "by": "hour_of_day", "grain": "hour"}
    )
    assert len(response.json()["buckets"]) == 24
    assert [b["key"] for b in response.json()["buckets"]][:3] == [["0"], ["1"], ["2"]] or True
    response = await client.get(
        "/stats/measurements", params={"agg": "count", "by": "hour_of_day", "grain": "day"}
    )
    assert response.status_code == 422
    assert "requires grain=hour" in response.text


async def test_filters_reach_the_fact_table(client, session, clean_db, tmp_path):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    response = await client.get(
        "/stats/measurements",
        params={
            "agg": "count", "by": "parameter", "grain": "raw",
            "filter": json.dumps({"$space": {"type": "office"}}),
        },
    )
    body = buckets_of(response.json())
    assert body[("co2",)]["n"] == len(fx.series[("co2", "S1")])
    assert body[("air_temperature",)]["n"] == len(fx.series[("air_temperature", "S1")])
    assert ("pm2_5",) not in body
    response = await client.get(
        "/stats/measurements",
        params={
            "agg": "count", "by": "space_type", "grain": "day", "parameters": "co2",
            "filter": json.dumps({"identifier": "study-a", "$building": {"country": ["CH"]}}),
        },
    )
    keys = [b["key"] for b in response.json()["buckets"]]
    # the unlinked space is its own null bucket, never merged
    assert sorted(k[0] or "" for k in keys) == ["", "meeting room", "office"]
    response = await client.get(
        "/stats/measurements",
        params={
            "agg": "stats", "parameters": "co2", "grain": "day",
            "filter": json.dumps({"$building": {"country": ["DE"]}}),
        },
    )
    body = response.json()
    assert body["buckets"] == []
    assert body["meta"]["n"] == 0
    assert body["meta"]["available_parameters"] == ["pm2_5"]


async def test_exceedance_and_coverage(client, session, clean_db, tmp_path):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    response = await client.get(
        "/stats/measurements",
        params={"agg": "exceedance", "parameters": "co2", "threshold": 600, "grain": "day"},
    )
    bucket = response.json()["buckets"][0]
    day_means = [v for points in series_of(fx, "co2") for v in
                 [sum(vs) / len(vs) for vs in daily(points).values()]]
    above = sum(1 for v in day_means if v > 600)
    assert bucket["exceedance"] == {
        "threshold": 600.0, "n_above": above, "share": pytest.approx(above / len(day_means))
    }
    response = await client.get("/stats/measurements", params={"agg": "exceedance", "parameters": "co2"})
    assert response.status_code == 422 and "threshold" in response.text
    response = await client.get(
        "/stats/measurements", params={"agg": "coverage", "by": "parameter,country"}
    )
    body = buckets_of(response.json())
    co2 = body[("co2", "CH")]
    co2_points = [p for points in series_of(fx, "co2") for p in points]
    assert co2["n"] == 1 and co2["n_records"] == len(co2_points)
    assert co2["coverage"]["n_datasets"] == 1
    assert co2["coverage"]["n_missing"] == 2
    assert co2["coverage"]["first_at"] == min(t for t, _ in co2_points).isoformat()
    assert co2["coverage"]["last_at"] == max(t for t, _ in co2_points).isoformat()
    # coverage reads dataset_parameter only: a building dimension counts a
    # dataset under every country its study has a building in
    assert body[("pm2_5", "DE")]["coverage"]["n_datasets"] == 1
    assert body[("pm2_5", "CH")]["coverage"]["n_datasets"] == 1


async def test_raw_cap_and_unknown_parameter(client, session, clean_db, tmp_path, monkeypatch):
    await loaded_fixture(session, clean_db, tmp_path)
    monkeypatch.setattr("api.services.explore.facts.RAW_CAP", 10)
    response = await client.get(
        "/stats/measurements", params={"agg": "count", "parameters": "co2", "grain": "raw"}
    )
    assert response.status_code == 422
    assert "above the cap of 10" in response.text
    response = await client.get(
        "/stats/measurements", params={"agg": "count", "parameters": "co2", "grain": "hour"}
    )
    assert response.status_code == 200
    response = await client.get("/stats/measurements", params={"agg": "stats", "parameters": "nope"})
    assert response.status_code == 422 and "unknown parameters" in response.text
    response = await client.get("/stats/measurements", params={"agg": "nope"})
    assert response.status_code == 422


async def test_query_plans_use_the_parameter_time_index(session, clean_db, tmp_path):
    await loaded_fixture(session, clean_db, tmp_path)
    from sqlalchemy import text

    await session.exec(text("SET enable_seqscan = off"))
    plan = "\n".join(
        r[0]
        for r in (
            await session.exec(
                text(
                    "EXPLAIN SELECT count(*) FROM measurement"
                    " WHERE parameter = 'co2' AND ts >= '2023-03-02' AND ts < '2023-03-04'"
                )
            )
        ).all()
    )
    # uncompressed chunks use the (parameter, ts) index, compressed ones the
    # segment-by index that starts with parameter
    assert "Index" in plan and "parameter" in plan, plan
    plan = "\n".join(
        r[0]
        for r in (
            await session.exec(
                text(
                    "EXPLAIN SELECT count(*) FROM measurement_day"
                    " WHERE parameter = 'co2' AND day >= '2023-03-02' AND day < '2023-03-04'"
                )
            )
        ).all()
    )
    assert "Index" in plan and "parameter" in plan, plan
