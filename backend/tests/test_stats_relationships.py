import json
import math
import statistics
from datetime import timedelta

import pytest
from api.models.catalog import Building, Dataset, Instrument, Space, Study
from api.models.explore import ExploreQuery
from api.services.explore.cache import cache
from api.services.explore.relationships import RelationshipService
from api.services.measurement import MeasurementService
from sqlalchemy import text
from tests.expected import paired_hours, regression, spearman
from tests.fixtures import START, mean, series_rows, write_csv
from tests.test_stats_metadata import buckets_of, loaded_fixture

STUDY_A = ("S1", "S2")
# study B: three spaces of one building, so that it reaches MIN_SPACES alone
DENSITY_B = {"S4": 0.5, "S5": 0.6, "S6": 0.8}


def co2_b(t, space: str) -> float:
    hours = (t - START).total_seconds() / 3600
    base = {"S4": 600, "S5": 650, "S6": 700}[space]
    return round(base + 150 * math.sin(hours / 12 * 2 * math.pi), 3)


def temperature_b(t, space: str) -> float:
    hours = (t - START).total_seconds() / 3600
    depth = {"S4": 0.5, "S5": 1.0, "S6": 1.5}[space]
    return round(24 - depth * math.sin(hours / 12 * 2 * math.pi + 0.3), 3)


async def with_study_b(session, engine, tmp_path):
    """The fixture (study A), and study B: CO2 and temperature every 10
    minutes in S4 to S6, related another way than in study A, so that the
    pooled r and the r of each study differ."""
    fx = await loaded_fixture(session, engine, tmp_path)
    study = Study(identifier="study-b", name="Study B")
    session.add(study)
    await session.commit()
    building = Building(identifier="B3", country="CH", type="office", study_id=study.id)
    session.add(building)
    await session.commit()
    dataset = Dataset(name="D3", description="co2 and temperature", study_id=study.id)
    session.add_all(
        [
            *(
                Space(
                    identifier=space,
                    type="office",
                    occupancy_density=density,
                    study_id=study.id,
                    building_id=building.id,
                )
                for space, density in DENSITY_B.items()
            ),
            Instrument(identifier="I1", study_id=study.id),
            dataset,
        ]
    )
    await session.commit()
    rows = []
    for space in DENSITY_B:
        for slug, unit, at in (
            ("co2", "ppm", co2_b),
            ("air_temperature", "°C", temperature_b),
        ):
            part, expected = series_rows(
                "D3",
                "B3",
                space,
                slug,
                unit,
                timedelta(minutes=10),
                lambda t, s=space, at=at: at(t, s),
            )
            fx.series[(slug, space)] = expected
            rows += part
    path = write_csv(tmp_path / "d3_long.csv", rows)
    await MeasurementService(engine).load(dataset.id, [path])
    cache.clear()
    return fx


def studies_of(bucket: dict) -> dict[str, dict]:
    """The studies of `within` by identifier."""
    return {study["study"]: study for study in bucket["within"]["studies"]}


def assert_within(bucket: dict, rs: dict[str, float | None]) -> None:
    """`within` against the r expected of each study by identifier, None for
    a study with no r of its own: the studies with an r first, by r, and the
    median of their r."""
    studies = bucket["within"]["studies"]
    assert bucket["n_studies"] == len(studies)
    assert {study["study"] for study in studies} == set(rs)
    ranked = sorted((r, study) for study, r in rs.items() if r is not None)
    assert [study["study"] for study in studies[: len(ranked)]] == [
        study for _, study in ranked
    ]
    for study in studies:
        expected = rs[study["study"]]
        if expected is None:
            assert "r" not in study, study
        else:
            assert study["r"] == pytest.approx(expected, rel=1e-6), study
    median = bucket["within"].get("median")
    if ranked:
        expected = statistics.median(r for r, _ in ranked)
        assert median == pytest.approx(expected, rel=1e-6)
    else:
        assert median is None


def density_points(fx, spaces) -> list[tuple[float, float]]:
    """(occupancy density, mean CO2) per space, the metric pairs."""
    density = {"S1": 0.1, "S2": 0.3, **DENSITY_B}
    return [(density[s], mean([v for _, v in fx.series[("co2", s)]])) for s in spaces]


@pytest.fixture(autouse=True)
def no_minimum(monkeypatch):
    """The fixture pairs two spaces: the tests below check the statistics,
    the `minimum` tests the cutoff."""
    monkeypatch.setattr("api.services.explore.relationships.MIN_SPACES", 1)
    monkeypatch.setattr("api.services.explore.relationships.MIN_PAIRS", 1)


def real_minimum(monkeypatch) -> None:
    monkeypatch.setattr("api.services.explore.relationships.MIN_SPACES", 3)
    monkeypatch.setattr("api.services.explore.relationships.MIN_PAIRS", 30)


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
        params={"agg": "pairs", "x": "space.occupancy_density", "y": "co2"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["meta"]["grain"] == "space"
    assert body["meta"]["parameters"] == ["co2"]
    bucket = body["buckets"][0]
    expected_points = sorted(
        (density, mean([v for _, v in fx.series[("co2", space)]]))
        for space, density in (("S1", 0.1), ("S2", 0.3))
    )
    assert bucket["n"] == 2
    assert_points(bucket["points"], expected_points)
    expected = regression(expected_points)
    assert bucket["fit"]["slope"] == pytest.approx(expected["slope"])
    assert bucket["fit"]["r2"] == pytest.approx(1.0)
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "space.nope", "y": "co2"},
    )
    assert response.status_code == 422
    # the metric is the explanatory variable: never y
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "co2", "y": "space.occupancy_density"},
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


async def test_partners(client, session, clean_db, tmp_path):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    response = await client.get(
        "/stats/relationships", params={"agg": "partners", "x": "co2"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["meta"]["parameters"] == ["co2"]
    # pm2_5 is only measured in S3, where there is no CO2
    expected = len(paired_hours(fx, "co2", "air_temperature", ("S1", "S2")))
    assert buckets_of(body) == {
        ("air_temperature",): {
            "key": ["air_temperature"],
            "n": expected,
            "n_spaces": 2,
            "enough": True,
        }
    }
    # the same count as the matrix cell of the pair
    response = await client.get(
        "/stats/relationships",
        params={"agg": "matrix", "parameters": "co2,air_temperature"},
    )
    assert response.json()["buckets"][0]["n"] == expected
    # measured alone: no partner
    response = await client.get(
        "/stats/relationships", params={"agg": "partners", "x": "pm2_5"}
    )
    assert response.json()["buckets"] == []
    for params in (
        {"agg": "partners"},
        {"agg": "partners", "x": "space.nope"},
        {"agg": "partners", "x": "co2", "by": "country"},
        {"agg": "partners", "x": "space.floor_area", "by": "country"},
    ):
        response = await client.get("/stats/relationships", params=params)
        assert response.status_code == 422, params


async def test_spearman_work_mem_is_for_its_query_only(session, clean_db, tmp_path):
    await loaded_fixture(session, clean_db, tmp_path)
    before = (await session.exec(text("SHOW work_mem"))).one()
    query = ExploreQuery(
        agg="matrix", parameters=["co2", "air_temperature"], method="spearman"
    )
    await RelationshipService(session).query(query, version=1)
    # the rest of the request's transaction runs at the default again
    assert (await session.exec(text("SHOW work_mem"))).one() == before


async def test_partnered(client, session, clean_db, tmp_path):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    response = await client.get("/stats/relationships", params={"agg": "partnered"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["meta"]["parameters"] == []
    # co2 and air_temperature share their hours; pm2_5 is measured alone
    expected = len(paired_hours(fx, "co2", "air_temperature", ("S1", "S2")))
    assert buckets_of(body) == {
        ("co2",): {"key": ["co2"], "n": expected},
        ("air_temperature",): {"key": ["air_temperature"], "n": expected},
    }
    # outside the range: no one has a partner
    response = await client.get(
        "/stats/relationships", params={"agg": "partnered", "from": "2024-01-01"}
    )
    assert response.json()["buckets"] == []
    response = await client.get(
        "/stats/relationships", params={"agg": "partnered", "by": "country"}
    )
    assert response.status_code == 422


async def test_partners_of_a_catalog_metric(client, session, clean_db, tmp_path):
    await loaded_fixture(session, clean_db, tmp_path)
    x = "space.occupancy_density"
    response = await client.get(
        "/stats/relationships", params={"agg": "partners", "x": x}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["meta"]["grain"] == "space"
    assert body["meta"]["parameters"] == []
    partners = buckets_of(body)
    # S1 and S2 have a density and CO2
    assert partners[("co2",)]["n"] == 2
    # each count is the number of points of the parameter's metric pairs
    for (slug,), bucket in partners.items():
        response = await client.get(
            "/stats/relationships", params={"agg": "pairs", "x": x, "y": slug}
        )
        assert response.json()["buckets"][0]["n"] == bucket["n"], slug
    # the filters apply: no space with a density in the German building
    response = await client.get(
        "/stats/relationships",
        params={
            "agg": "partners",
            "x": x,
            "filter": json.dumps({"$building": {"country": ["DE"]}}),
        },
    )
    assert response.json()["buckets"] == []


async def test_minimum_pairs_have_counts_but_no_fit(
    client, session, clean_db, tmp_path, monkeypatch
):
    """#226: CO2 and temperature share many hours, but in two spaces only."""
    fx = await loaded_fixture(session, clean_db, tmp_path)
    real_minimum(monkeypatch)
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "co2", "y": "air_temperature"},
    )
    assert response.status_code == 200, response.text
    bucket = response.json()["buckets"][0]
    expected_points = paired_hours(fx, "co2", "air_temperature", ("S1", "S2"))
    assert bucket["n"] == len(expected_points) > 30
    assert bucket["n_spaces"] == 2
    assert bucket["enough"] is False
    assert bucket["fit"] == {}
    # the dots stay: the chart shows them without a line
    assert_points(bucket["points"], expected_points)
    # enough spaces, too few pairs
    monkeypatch.setattr("api.services.explore.relationships.MIN_SPACES", 2)
    monkeypatch.setattr(
        "api.services.explore.relationships.MIN_PAIRS", len(expected_points) + 1
    )
    from api.services.explore.cache import cache

    cache.clear()
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "co2", "y": "air_temperature"},
    )
    assert response.json()["buckets"][0]["enough"] is False


async def test_minimum_metric_pairs_from_two_spaces(
    client, session, clean_db, tmp_path, monkeypatch
):
    """#226: a pollutant against a space metric got r = 0.00 from one space."""
    await loaded_fixture(session, clean_db, tmp_path)
    real_minimum(monkeypatch)
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "space.occupancy_density", "y": "co2"},
    )
    assert response.status_code == 200, response.text
    bucket = response.json()["buckets"][0]
    assert (bucket["n"], bucket["n_spaces"], bucket["enough"]) == (2, 2, False)
    assert bucket["fit"] == {}
    assert len(bucket["points"]) == 2
    response = await client.get(
        "/stats/relationships",
        params={"agg": "partners", "x": "space.occupancy_density"},
    )
    co2 = buckets_of(response.json())[("co2",)]
    assert (co2["n_spaces"], co2["enough"]) == (2, False)


async def test_minimum_matrix_cells_are_blank(
    client, session, clean_db, tmp_path, monkeypatch
):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    real_minimum(monkeypatch)
    n = len(paired_hours(fx, "air_temperature", "co2", ("S1", "S2")))
    for method in ("pearson", "spearman"):
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
        cell = cells[("air_temperature", "co2")]
        assert (cell["n"], cell["n_spaces"], cell["enough"]) == (n, 2, False), method
        assert "r" not in cell["fit"], method
        never = cells[("co2", "pm2_5")]
        assert (never["n"], never["n_spaces"], never["enough"]) == (0, 0, False)
    response = await client.get(
        "/stats/relationships", params={"agg": "partners", "x": "co2"}
    )
    partner = buckets_of(response.json())[("air_temperature",)]
    assert (partner["n"], partner["n_spaces"], partner["enough"]) == (n, 2, False)


async def test_pairs_within_each_study(client, session, clean_db, tmp_path):
    """#229: a pooled r can come from the differences between studies."""
    fx = await with_study_b(session, clean_db, tmp_path)
    study_b = tuple(DENSITY_B)
    params = {"agg": "pairs", "x": "co2", "y": "air_temperature"}
    response = await client.get("/stats/relationships", params=params)
    assert response.status_code == 200, response.text
    bucket = response.json()["buckets"][0]
    pooled = paired_hours(fx, "co2", "air_temperature", STUDY_A + study_b)
    assert (bucket["n"], bucket["n_spaces"], bucket["n_studies"]) == (len(pooled), 5, 2)
    assert bucket["fit"]["r"] == pytest.approx(regression(pooled)["r"], rel=1e-6)
    r_a, r_b = (
        regression(paired_hours(fx, "co2", "air_temperature", spaces))["r"]
        for spaces in (STUDY_A, study_b)
    )
    assert_within(bucket, {"study-a": r_a, "study-b": r_b})
    studies = studies_of(bucket)
    for study, spaces in (("study-a", STUDY_A), ("study-b", study_b)):
        n = len(paired_hours(fx, "co2", "air_temperature", spaces))
        assert (studies[study]["n"], studies[study]["n_spaces"]) == (n, len(spaces))
        assert studies[study]["enough"] is True
    # per bucket of `by`: the offices are in both studies, the meeting room in A
    response = await client.get(
        "/stats/relationships", params={**params, "by": "space_type"}
    )
    buckets = buckets_of(response.json())
    office = buckets[("office",)]
    assert (office["n_spaces"], office["n_studies"]) == (4, 2)
    r_s1 = regression(paired_hours(fx, "co2", "air_temperature", ("S1",)))["r"]
    assert_within(office, {"study-a": r_s1, "study-b": r_b})
    room = buckets[("meeting room",)]
    assert (room["n_spaces"], room["n_studies"]) == (1, 1)
    assert_within(room, {"study-a": room["fit"]["r"]})


async def test_metric_pairs_within_each_study(client, session, clean_db, tmp_path):
    fx = await with_study_b(session, clean_db, tmp_path)
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "space.occupancy_density", "y": "co2"},
    )
    assert response.status_code == 200, response.text
    bucket = response.json()["buckets"][0]
    assert (bucket["n"], bucket["n_spaces"], bucket["n_studies"]) == (5, 5, 2)
    pooled = density_points(fx, STUDY_A + tuple(DENSITY_B))
    assert bucket["fit"]["r"] == pytest.approx(regression(pooled)["r"], rel=1e-6)
    assert_points(bucket["points"], pooled)
    assert_within(
        bucket,
        {
            study: regression(density_points(fx, spaces))["r"]
            for study, spaces in (("study-a", STUDY_A), ("study-b", tuple(DENSITY_B)))
        },
    )
    studies = studies_of(bucket)
    # one point per space
    assert (studies["study-a"]["n"], studies["study-a"]["n_spaces"]) == (2, 2)
    assert (studies["study-b"]["n"], studies["study-b"]["n_spaces"]) == (3, 3)


async def test_matrix_within_each_study(client, session, clean_db, tmp_path):
    fx = await with_study_b(session, clean_db, tmp_path)
    study_b = tuple(DENSITY_B)
    pooled = paired_hours(fx, "air_temperature", "co2", STUDY_A + study_b)
    per_study = [
        paired_hours(fx, "air_temperature", "co2", spaces)
        for spaces in (STUDY_A, study_b)
    ]
    for method, r_of in (
        ("pearson", lambda points: regression(points)["r"]),
        ("spearman", spearman),
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
        cell = cells[("air_temperature", "co2")]
        assert (cell["n"], cell["n_spaces"], cell["n_studies"]) == (len(pooled), 5, 2)
        assert cell["fit"]["r"] == pytest.approx(r_of(pooled), rel=1e-6), method
        r_a, r_b = (r_of(points) for points in per_study)
        assert_within(cell, {"study-a": r_a, "study-b": r_b})
        studies = studies_of(cell)
        assert [studies[s]["n"] for s in ("study-a", "study-b")] == [
            len(points) for points in per_study
        ], method
        # never measured together: no study, no r
        never = cells[("co2", "pm2_5")]
        assert (never["n_studies"], never["within"]) == (0, {"studies": []}), method


async def test_minimum_within_each_study(
    client, session, clean_db, tmp_path, monkeypatch
):
    """Study A has two spaces: it counts in n_studies, with no r of its own."""
    fx = await with_study_b(session, clean_db, tmp_path)
    real_minimum(monkeypatch)
    study_b = tuple(DENSITY_B)
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "co2", "y": "air_temperature"},
    )
    bucket = response.json()["buckets"][0]
    assert (bucket["enough"], bucket["n_studies"]) == (True, 2)
    r_b = regression(paired_hours(fx, "co2", "air_temperature", study_b))["r"]
    assert_within(bucket, {"study-a": None, "study-b": r_b})
    assert studies_of(bucket)["study-a"]["enough"] is False
    response = await client.get(
        "/stats/relationships",
        params={"agg": "pairs", "x": "space.occupancy_density", "y": "co2"},
    )
    bucket = response.json()["buckets"][0]
    assert (bucket["enough"], bucket["n_studies"]) == (True, 2)
    r_b = regression(density_points(fx, study_b))["r"]
    assert_within(bucket, {"study-a": None, "study-b": r_b})
    points = paired_hours(fx, "air_temperature", "co2", study_b)
    for method, r_b in (
        ("pearson", regression(points)["r"]),
        ("spearman", spearman(points)),
    ):
        response = await client.get(
            "/stats/relationships",
            params={
                "agg": "matrix",
                "parameters": "co2,air_temperature",
                "method": method,
            },
        )
        cell = response.json()["buckets"][0]
        assert (cell["enough"], cell["n_studies"]) == (True, 2), method
        assert_within(cell, {"study-a": None, "study-b": r_b})
        assert studies_of(cell)["study-a"]["enough"] is False, method


async def test_pairs_spearman(client, session, clean_db, tmp_path):
    """`pairs` takes the method for r and the r of each study; the
    least-squares fit stays over the values."""
    fx = await with_study_b(session, clean_db, tmp_path)
    study_b = tuple(DENSITY_B)
    for x, y, points_of in (
        (
            "co2",
            "air_temperature",
            lambda s: paired_hours(fx, "co2", "air_temperature", s),
        ),
        ("space.occupancy_density", "co2", lambda s: density_points(fx, s)),
    ):
        params = {"agg": "pairs", "x": x, "y": y}
        pearson = (await client.get("/stats/relationships", params=params)).json()
        response = await client.get(
            "/stats/relationships", params={**params, "method": "spearman"}
        )
        assert response.status_code == 200, response.text
        bucket = response.json()["buckets"][0]
        assert bucket["fit"]["r"] == pytest.approx(
            spearman(points_of(STUDY_A + study_b)), rel=1e-6
        ), x
        assert_within(
            bucket,
            {
                "study-a": spearman(points_of(STUDY_A)),
                "study-b": spearman(points_of(study_b)),
            },
        )
        for name in ("slope", "intercept", "r2"):
            expected = pearson["buckets"][0]["fit"][name]
            assert bucket["fit"][name] == pytest.approx(expected), (x, name)
        assert bucket["points"] == pearson["buckets"][0]["points"], x


async def test_pairs_split_ranks_inside_each_bucket(
    client, session, clean_db, tmp_path
):
    """By space type, the office bucket holds S1 of study A and the spaces of
    study B: Spearman ranks inside the bucket, and inside the bucket and the
    study."""
    fx = await with_study_b(session, clean_db, tmp_path)
    study_b = tuple(DENSITY_B)
    response = await client.get(
        "/stats/relationships",
        params={
            "agg": "pairs",
            "x": "co2",
            "y": "air_temperature",
            "by": "space_type",
            "method": "spearman",
        },
    )
    assert response.status_code == 200, response.text
    buckets = buckets_of(response.json())
    assert set(buckets) == {("office",), ("meeting room",)}

    def hours(spaces):
        return paired_hours(fx, "co2", "air_temperature", spaces)

    office = buckets[("office",)]
    assert office["fit"]["r"] == pytest.approx(spearman(hours(("S1",) + study_b)))
    assert_within(
        office,
        {"study-a": spearman(hours(("S1",))), "study-b": spearman(hours(study_b))},
    )
    meeting = buckets[("meeting room",)]
    assert meeting["fit"]["r"] == pytest.approx(spearman(hours(("S2",))))
    assert_within(meeting, {"study-a": spearman(hours(("S2",)))})


async def test_pairs_split_by_ventilation(client, session, clean_db, tmp_path):
    """Building B1 is mechanically ventilated, B3 of study B has no answer:
    one bucket each, with the points and the fit of its own spaces."""
    fx = await with_study_b(session, clean_db, tmp_path)
    study_b = tuple(DENSITY_B)
    for x, y, points_of in (
        (
            "co2",
            "air_temperature",
            lambda s: paired_hours(fx, "co2", "air_temperature", s),
        ),
        ("space.occupancy_density", "co2", lambda s: density_points(fx, s)),
    ):
        response = await client.get(
            "/stats/relationships",
            params={"agg": "pairs", "x": x, "y": y, "by": "ventilation"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["meta"]["dimensions"] == ["ventilation"]
        # nulls last
        assert [bucket["key"] for bucket in body["buckets"]] == [["yes"], [None]], x
        for bucket, spaces, study in zip(
            body["buckets"], (STUDY_A, study_b), ("study-a", "study-b")
        ):
            expected = points_of(spaces)
            assert bucket["n"] == len(expected), x
            assert bucket["fit"]["r"] == pytest.approx(regression(expected)["r"]), x
            assert_points(bucket["points"], expected)
            assert [s["study"] for s in bucket["within"]["studies"]] == [study]


async def test_pairs_sampled_per_bucket(
    client, session, clean_db, tmp_path, monkeypatch
):
    """The buckets share SAMPLE: each keeps every ceil(n / quota)-th row, and
    a bucket below its quota keeps all its rows."""
    fx = await with_study_b(session, clean_db, tmp_path)
    params = {"agg": "pairs", "x": "co2", "y": "air_temperature", "by": "space_type"}
    full = buckets_of((await client.get("/stats/relationships", params=params)).json())
    meeting_n = full[("meeting room",)]["n"]
    office_n = full[("office",)]["n"]
    assert meeting_n < office_n
    # the meeting room fits in its half of SAMPLE, the offices do not
    sample = 2 * meeting_n
    monkeypatch.setattr("api.services.explore.relationships.SAMPLE", sample)
    cache.clear()
    buckets = buckets_of(
        (await client.get("/stats/relationships", params=params)).json()
    )
    meeting = buckets[("meeting room",)]
    assert meeting["sampled"] is False
    assert_points(
        meeting["points"], paired_hours(fx, "co2", "air_temperature", ("S2",))
    )
    office = buckets[("office",)]
    quota = meeting_n
    step = math.ceil(office_n / quota)
    assert office["sampled"] is True
    assert len(office["points"]) == math.ceil(office_n / step)
    assert office["fit"] == pytest.approx(full[("office",)]["fit"])
