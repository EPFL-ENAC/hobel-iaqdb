from api.services.benchmark import BenchmarkService, parse_benchmarks
from api.services.explore.cache import cache
from api.services.explore.dimensions import DIMENSIONS
from api.services.parameter import read_parameters
from tests.test_benchmarks import benchmark_row


async def test_schema_lists_dimensions_parameters_and_version(client, session):
    parameters = {p.slug: p for p in read_parameters()}
    pm25 = {"parameter": "pm2_5", "unit": "µg/m³", "value": "15"}
    rows = [
        benchmark_row("pm-1", "false", **pm25, region="France"),
        benchmark_row("pm-2", **pm25, averaging="day", region="Worldwide"),
        benchmark_row("pm-3", "false", **pm25, region="austria"),
        benchmark_row("pm-4", "false", **pm25, region="Worldwide"),
        benchmark_row(
            "radon-1", parameter="radon", unit="Bq/m³", averaging="long_term"
        ),
    ]
    await BenchmarkService(session).replace(parse_benchmarks(rows, parameters))
    await session.commit()
    cache.clear()
    response = await client.get("/stats/schema")
    assert response.status_code == 200
    body = response.json()
    assert {d["key"] for d in body["dimensions"]} == set(DIMENSIONS)
    country = next(d for d in body["dimensions"] if d["key"] == "country")
    assert country == {
        "key": "country",
        "label": "Country",
        "entity": "building",
        "filter_path": "$building.country",
        "drill_to": "city",
        "kind": "category",
    }
    assert len(body["parameters"]) == len(read_parameters())
    pm25 = next(p for p in body["parameters"] if p["slug"] == "pm2_5")
    assert pm25["unit"] == "µg/m³"
    default = pm25["benchmarks"][0]
    assert default["is_default"] and default["id"] == "pm-2"
    assert default["institution"] == "CEN" and default["region"] == "Worldwide"
    assert (default["averaging"], default["grain"], default["value"]) == (
        "day",
        "day",
        15,
    )
    assert default["url"].startswith("https://")
    # worldwide references come right after the default, then by region
    assert [b["id"] for b in pm25["benchmarks"]] == ["pm-2", "pm-4", "pm-3", "pm-1"]
    radon = next(p for p in body["parameters"] if p["slug"] == "radon")
    assert {b["grain"] for b in radon["benchmarks"]} == {"space"}
    co2 = next(p for p in body["parameters"] if p["slug"] == "co2")
    assert co2["benchmarks"] == []
    assert "space.occupancy_density" in body["metrics"]
    # the import bumped the version
    assert body["version"] == 2


async def test_schema_etag_and_304(client):
    first = await client.get("/stats/schema")
    etag = first.headers["etag"]
    assert first.headers["cache-control"] == "private, max-age=300"
    again = await client.get("/stats/schema", headers={"If-None-Match": etag})
    assert again.status_code == 304
    assert again.headers["etag"] == etag


async def test_frequencies_routes_are_gone(client):
    for entity in ("studies", "buildings", "spaces"):
        response = await client.get(
            f"/stats/frequencies/{entity}", params={"by": "type"}
        )
        assert response.status_code == 404
