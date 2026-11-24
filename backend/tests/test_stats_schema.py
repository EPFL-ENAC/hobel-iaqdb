from api.services.explore.dimensions import DIMENSIONS
from api.services.parameter import read_parameters


async def test_schema_lists_dimensions_parameters_and_version(client):
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
    assert default["institution"] == "WHO" and default["region"] == "Worldwide"
    assert (default["averaging"], default["grain"], default["value"]) == (
        "day",
        "day",
        15,
    )
    assert default["url"].startswith("https://")
    assert not any(b["is_default"] for b in pm25["benchmarks"][1:])
    # worldwide references come right after the default
    regions = [b["region"] for b in pm25["benchmarks"][1:]]
    assert regions == sorted(regions, key=lambda r: (r != "Worldwide", r.casefold()))
    radon = next(p for p in body["parameters"] if p["slug"] == "radon")
    assert {b["grain"] for b in radon["benchmarks"]} == {"space"}
    assert "space.occupancy_density" in body["metrics"]
    assert body["version"] == 1


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
