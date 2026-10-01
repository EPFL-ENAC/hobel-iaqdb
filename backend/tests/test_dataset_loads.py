"""Admin listing of the dataset measurement loads; load details stay private."""

from api.models.catalog import Dataset, Study
from api.services.dataset import DatasetService


async def test_dataset_loads(session, client):
    a = Study(identifier="study-a", name="Alpha")
    b = Study(identifier="study-b", name="Beta")
    session.add_all([a, b])
    await session.commit()
    session.add_all(
        [
            Dataset(
                name="D1",
                description="",
                study_id=a.id,
                summary_status="ready",
                load_report={"loaded": 3},
            ),
            Dataset(
                name="D2",
                description="",
                study_id=a.id,
                summary_status="failed",
                summary_error="no CSV file in the dataset folder",
            ),
            Dataset(name="D3_x", description="", study_id=b.id),
        ]
    )
    await session.commit()
    service = DatasetService(session)

    async def names(**kwargs):
        args = {"status": None, "study_id": None, "q": None, "skip": 0, "limit": 25}
        result = await service.find_loads(**{**args, **kwargs})
        return result.total, [d.name for d in result.data]

    assert await names() == (3, ["D1", "D2", "D3_x"])
    assert await names(status="failed") == (1, ["D2"])
    assert await names(study_id=b.id) == (1, ["D3_x"])
    assert await names(q="csv FILE") == (1, ["D2"])
    assert await names(q="beta") == (1, ["D3_x"])
    assert await names(q="study-a", status="ready") == (1, ["D1"])
    # `_` is literal, not a wildcard
    assert await names(q="3_") == (1, ["D3_x"])
    assert await names(q="1_") == (0, [])
    assert await names(skip=1, limit=1) == (3, ["D2"])
    row = (await service.find_loads("ready", None, None, 0, 25)).data[0]
    assert row.study_name == "Alpha" and row.load_report == {"loaded": 3}

    # admins only
    assert (await client.get("/contribute/dataset-loads")).status_code in (401, 403)
    # public reads carry the status only
    public = (await client.get("/catalog/datasets")).json()["data"]
    assert {d["summary_status"] for d in public} == {"ready", "failed", "pending"}
    assert all("summary_error" not in d and "load_report" not in d for d in public)
    study = (await client.get(f"/catalog/study/{a.id}")).json()
    assert all("summary_error" not in d for d in study["datasets"])
    dataset = (
        await client.get(f"/catalog/dataset/{study['datasets'][0]['id']}")
    ).json()
    assert "load_report" not in dataset
