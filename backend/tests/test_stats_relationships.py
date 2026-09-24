import json

import pytest
from tests.expected import paired_hours, regression, spearman
from tests.fixtures import mean
from tests.test_stats_metadata import buckets_of, loaded_fixture


def assert_points(got: list, expected: list) -> None:
    assert len(got) == len(expected)
    for g, e in zip(sorted(map(tuple, got)), sorted(expected)):
        assert g == pytest.approx(e, rel=1e-6)


async def test_pairs_fit_and_points(client, session, clean_db, tmp_path):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "co2", "y": "air_temperature"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["meta"]["grain"] == "hour"
    assert body["meta"]["parameters"] == ["co2", "air_temperature"]
    assert "unit" not in body["meta"]
    bucket = body["buckets"][0]
    expected_points = paired_hours(fx, "co2", "air_temperature", ("S1", "S2"))
    expected = regression(expected_points)
    assert bucket["n"] == expected["n"]
    assert bucket["sampled"] is False
    for name in ("slope", "intercept", "r", "r2"):
        assert bucket["fit"][name] == pytest.approx(expected[name], rel=1e-6)
    assert_points(bucket["points"], expected_points)
    # by space type: one bucket per space, order by n desc then key
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "co2", "y": "air_temperature", "by": "space_type"},
    )
    buckets = buckets_of(response.json())
    for space, key in (("S1", "office"), ("S2", "meeting room")):
        expected = regression(paired_hours(fx, "co2", "air_temperature", (space,)))
        assert buckets[(key,)]["n"] == expected["n"]
        assert buckets[(key,)]["fit"]["r"] == pytest.approx(expected["r"])


async def test_pairs_sampling_is_deterministic(
    client, session, clean_db, tmp_path, monkeypatch
):
    await loaded_fixture(session, clean_db, tmp_path)
    monkeypatch.setattr("api.services.explore.relationships.SAMPLE", 20)
    params = {"agg": "pairs", "x": "co2", "y": "air_temperature", "grain": "raw"}
    first = (await client.get("/stats/relationships", params=params)).json()["buckets"][
        0
    ]
    from api.services.explore.cache import cache

    cache.clear()
    second = (await client.get("/stats/relationships", params=params)).json()[
        "buckets"
    ][0]
    assert first["sampled"] is True
    assert first["n"] > 20 and len(first["points"]) <= 21
    assert first["points"] == second["points"]
    assert first["fit"] == second["fit"]


async def test_pairs_with_a_catalog_metric(client, session, clean_db, tmp_path):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "co2", "y": "space.occupancy_density"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["meta"]["grain"] == "space"
    assert body["meta"]["parameters"] == ["co2"]
    bucket = body["buckets"][0]
    expected_points = sorted(
        (mean([v for _, v in fx.series[("co2", space)]]), density)
        for space, density in (("S1", 0.1), ("S2", 0.3))
    )
    assert bucket["n"] == 2
    assert_points(bucket["points"], expected_points)
    expected = regression(expected_points)
    assert bucket["fit"]["slope"] == pytest.approx(expected["slope"])
    assert bucket["fit"]["r2"] == pytest.approx(1.0)
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "co2", "y": "space.nope"},
    )
    assert response.status_code == 422


async def test_matrix_pearson_and_spearman(client, session, clean_db, tmp_path):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    points = paired_hours(fx, "air_temperature", "co2", ("S1", "S2"))
    for method, expected_r in (
        ("pearson", regression(points)["r"]),
        ("spearman", spearman(points)),
    ):
        response = await client.get(
            "/stats/relationships",
            params={
                "agg": "matrix",
                "parameters": "co2,air_temperature,pm2_5",
                "method": method,
            },
        )
        assert response.status_code == 200, response.text
        cells = buckets_of(response.json())
        assert set(cells) == {
            ("air_temperature", "co2"),
            ("air_temperature", "pm2_5"),
            ("co2", "pm2_5"),
        }
        cell = cells[("air_temperature", "co2")]
        assert cell["n"] == len(points)
        assert cell["fit"]["r"] == pytest.approx(expected_r, rel=1e-6), method
        assert cells[("co2", "pm2_5")]["n"] == 0
        assert "r" not in cells[("co2", "pm2_5")]["fit"]
    response = await client.get(
        "/stats/relationships", params={"agg": "matrix", "parameters": "co2"}
    )
    assert response.status_code == 422
    response = await client.get(
        "/stats/relationships", params={"agg": "pairs", "x": "co2"}
    )
    assert response.status_code == 422


async def test_matrix_empty_state(client, session, clean_db, tmp_path):
    await loaded_fixture(session, clean_db, tmp_path)
    # the German building only has PM2.5, so no pair has co-timed rows
    response = await client.get(
        "/stats/relationships",
        params={
            "agg": "matrix",
            "parameters": "co2,air_temperature",
            "filter": json.dumps({"$building": {"country": ["DE"]}}),
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["buckets"] == []
    assert body["meta"]["n"] == 0
    assert body["meta"]["available_parameters"] == ["pm2_5"]
