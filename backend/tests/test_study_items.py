"""Study sub-listings are paged and sorted server-side."""

import json

from tests.fixtures import make_catalog


async def test_study_buildings_paged_and_sorted(session, client):
    fx = await make_catalog(session)
    params = {"range": json.dumps([0, 0]), "sort": json.dumps(["identifier", "DESC"])}
    res = await client.get(f"/catalog/study/{fx.study_id}/buildings", params=params)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    assert [b["identifier"] for b in body["data"]] == ["B2"]
    assert [s["identifier"] for s in body["data"][0]["spaces"]] == ["S3"]

    res = await client.get(f"/catalog/study/{fx.study_id}/datasets")
    assert res.json()["total"] == 2 and len(res.json()["data"]) == 2
