import json

from api.models.catalog import Building, Variable
from api.services.explore.cache import cache
from api.services.measurement import MeasurementService
from tests.fixtures import make_catalog, make_fixture


async def loaded_fixture(session, engine, tmp_path):
    cache.clear()
    fx = await make_fixture(session, tmp_path)
    service = MeasurementService(engine)
    for name, paths in fx.files.items():
        await service.load(fx.datasets[name], paths)
    return fx


def buckets_of(body: dict) -> dict:
    return {tuple(b["key"]): b for b in body["buckets"]}


async def test_count_by_dimension(client, session, clean_db, tmp_path):
    await loaded_fixture(session, clean_db, tmp_path)
    response = await client.get(
        "/stats/metadata", params={"entity": "buildings", "by": "country"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"] == {
        "source": "metadata",
        "agg": "count",
        "grain": "entity",
        "dimensions": ["country"],
        "parameters": [],
        "n": 2,
        "version": 1,
    }
    assert body["buckets"] == [
        {"key": ["CH"], "n": 1},
        {"key": ["DE"], "n": 1},
    ]
    response = await client.get(
        "/stats/metadata", params={"entity": "spaces", "by": "ventilation_type,country"}
    )
    assert buckets_of(response.json()) == {
        ("natural", "CH"): {"key": ["natural", "CH"], "n": 1},
        ("natural", "DE"): {"key": ["natural", "DE"], "n": 1},
        ("mechanical", "CH"): {"key": ["mechanical", "CH"], "n": 1},
    }
    # the order is deterministic: n desc then key
    assert [b["key"] for b in response.json()["buckets"]] == [
        ["mechanical", "CH"],
        ["natural", "CH"],
        ["natural", "DE"],
    ]


async def test_count_datasets_with_parameter_and_filter(
    client, session, clean_db, tmp_path
):
    await loaded_fixture(session, clean_db, tmp_path)
    response = await client.get(
        "/stats/metadata",
        params={"entity": "datasets", "by": "parameter", "parameters": "co2,pm2_5"},
    )
    assert buckets_of(response.json()) == {
        ("co2",): {"key": ["co2"], "n": 1},
        ("pm2_5",): {"key": ["pm2_5"], "n": 1},
    }
    assert "unit" not in response.json()["meta"]
    response = await client.get(
        "/stats/metadata",
        params={
            "entity": "datasets",
            "by": "country",
            "filter": json.dumps({"$building": {"country": ["DE"]}}),
        },
    )
    assert response.json()["buckets"] == [{"key": ["DE"], "n": 2}]
    response = await client.get(
        "/stats/metadata",
        params={
            "entity": "studies",
            "by": "climate_zone",
            "filter": json.dumps({"identifier": ["nope"]}),
            "parameters": "co2",
        },
    )
    body = response.json()
    assert body["buckets"] == []
    assert body["meta"]["n"] == 0
    assert body["meta"]["available_parameters"] == []


async def test_empty_state_lists_available_parameters(
    client, session, clean_db, tmp_path
):
    await loaded_fixture(session, clean_db, tmp_path)
    response = await client.get(
        "/stats/metadata",
        params={"entity": "datasets", "by": "country", "parameters": "radon"},
    )
    body = response.json()
    assert body["buckets"] == []
    assert body["meta"]["available_parameters"] == ["air_temperature", "co2", "pm2_5"]


async def test_availability(client, session, clean_db, tmp_path):
    await loaded_fixture(session, clean_db, tmp_path)
    response = await client.get(
        "/stats/metadata",
        params={
            "entity": "buildings",
            "agg": "availability",
            "fields": "climate_zone,timezone,construction_year",
        },
    )
    assert response.status_code == 200
    assert buckets_of(response.json()) == {
        ("climate_zone",): {
            "key": ["climate_zone"],
            "n": 2,
            "availability": {"present": 2, "total": 2},
        },
        ("construction_year",): {
            "key": ["construction_year"],
            "n": 1,
            "availability": {"present": 1, "total": 2},
        },
        ("timezone",): {
            "key": ["timezone"],
            "n": 0,
            "availability": {"present": 0, "total": 2},
        },
    }
    response = await client.get(
        "/stats/metadata", params={"entity": "spaces", "agg": "availability"}
    )
    keys = {b["key"][0] for b in response.json()["buckets"]}
    assert "occupancy_density" in keys and "id" not in keys and "identifier" not in keys


async def test_variable_availability(client, session, clean_db):
    cache.clear()
    fx = await make_catalog(session)
    d1, d2 = fx.datasets["D1"], fx.datasets["D2"]
    session.add_all(
        [
            Variable(
                name="co2",
                type="float",
                unit="ppm",
                reference="co2",
                study_id=fx.study_id,
                dataset_id=d1,
            ),
            Variable(
                name="t",
                type="float",
                reference="air_temperature",
                study_id=fx.study_id,
                dataset_id=d1,
            ),
            Variable(name="pm", type="float", study_id=fx.study_id, dataset_id=d2),
        ]
    )
    await session.commit()
    response = await client.get(
        "/stats/metadata", params={"entity": "variables", "agg": "availability"}
    )
    assert response.status_code == 200
    availability = {b["key"][0]: b["availability"] for b in response.json()["buckets"]}
    assert availability == {
        "unit": {"present": 1, "total": 3},
        "format": {"present": 0, "total": 3},
        "reference": {"present": 2, "total": 3},
    }
    # the study's filters reach its variables
    response = await client.get(
        "/stats/metadata",
        params={
            "entity": "variables",
            "agg": "availability",
            "filter": json.dumps({"$building": {"country": "FR"}}),
        },
    )
    assert {b["availability"]["total"] for b in response.json()["buckets"]} == {0}


async def test_building_descriptor_and_band_dimensions(client, session, clean_db):
    cache.clear()
    fx = await make_catalog(session)
    b1 = await session.get(Building, fx.buildings["B1"])
    b1.outdoor_env = "urban"
    session.add(b1)
    await session.commit()

    async def counts(by: str) -> dict:
        response = await client.get(
            "/stats/metadata", params={"entity": "buildings", "by": by}
        )
        assert response.status_code == 200
        return {b["key"][0]: b["n"] for b in response.json()["buckets"]}

    assert await counts("outdoor_env") == {"urban": 1, None: 1}
    # B1 stands at 400 m, built in 1990; B2 has neither
    assert await counts("altitude_band") == {"250": 1, None: 1}
    assert await counts("construction_decade") == {"1990": 1, None: 1}
    # a descriptor dimension is a filter too
    response = await client.get(
        "/stats/metadata",
        params={
            "entity": "buildings",
            "by": "country",
            "filter": json.dumps({"$building": {"outdoor_env": "urban"}}),
        },
    )
    assert [b["key"] for b in response.json()["buckets"]] == [["CH"]]


async def test_validation_errors(client, session, clean_db, tmp_path):
    await loaded_fixture(session, clean_db, tmp_path)
    cases = [
        ({"by": "country"}, "entity is required"),
        ({"entity": "buildings", "by": "nope"}, "unknown dimension"),
        ({"entity": "buildings", "by": "month"}, "time dimensions"),
        ({"entity": "buildings", "parameters": "xyz"}, "unknown parameters"),
        ({"entity": "buildings", "by": "a,b,c"}, "at most 2"),
        ({"entity": "buildings", "filter": "{"}, "not JSON"),
        (
            {"entity": "buildings", "filter": json.dumps({"$building": {"nope": 1}})},
            "unknown filter field",
        ),
        (
            {"entity": "buildings", "agg": "availability", "fields": "nope"},
            "unknown fields",
        ),
    ]
    for params, message in cases:
        response = await client.get("/stats/metadata", params=params)
        assert response.status_code == 422, params
        assert message in json.dumps(response.json()), params


async def test_cache_etag_and_version(client, session, clean_db, tmp_path):
    await loaded_fixture(session, clean_db, tmp_path)
    params = {"entity": "buildings", "by": "country"}
    first = await client.get("/stats/metadata", params=params)
    etag = first.headers["etag"]
    cached = await client.get(
        "/stats/metadata", params=params, headers={"If-None-Match": etag}
    )
    assert cached.status_code == 304
    # the same query with keys in another order and a canonical-equivalent
    # filter hits the same entry
    same = await client.get(
        "/stats/metadata",
        params={"by": "country", "entity": "buildings", "filter": "{}"},
    )
    assert same.headers["etag"] == etag
    # a data change bumps the version and the ETag
    from api.services.catalog_version import CatalogVersionService

    await CatalogVersionService(session).bump()
    await session.commit()
    bumped = await client.get("/stats/metadata", params=params)
    assert bumped.headers["etag"] != etag
    assert bumped.json()["meta"]["version"] == 2
