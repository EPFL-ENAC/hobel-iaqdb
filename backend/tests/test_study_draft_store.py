"""Study drafts in the database and the S3 files index."""

import json

from api.models.catalog import StudyDraft
from api.scripts import import_s3_drafts
from api.services import study as study_module
from api.services import study_draft as draft_module
from api.services.contribution import ContributionService
from api.services.s3 import s3_client
from api.services.study import StudyService
from api.services.study_draft import StudyDraftService
from api.services.study_file import StudyFileService


def draft_key(identifier: str, name: str) -> str:
    return s3_client.to_s3_key(f"draft/{identifier}/files/D1/{name}")


def document(identifier: str, *paths: str) -> dict:
    return {
        "identifier": identifier,
        "name": "Study A",
        "unknown": {"kept": True},
        "datasets": [
            {
                "name": "D1",
                "description": "d1",
                "folder": {"children": [{"name": p, "path": p} for p in paths]},
            }
        ],
    }


async def test_draft_round_trip_and_files_index(session, monkeypatch):
    deleted = []

    async def fake_delete(keys):
        deleted.extend(keys)

    monkeypatch.setattr(draft_module, "delete_objects", fake_delete)
    service = StudyDraftService(session)
    files = StudyFileService(session)
    a, b = draft_key("s1", "a.csv"), draft_key("s1", "b.csv")

    # files outside the draft folder are not indexed
    saved = await service.createOrUpdate(document("s1", a, "elsewhere/x.csv"))
    assert saved["datasets"][0]["folder"]["name"] == "D1"
    assert await files.keys("s1", "draft") == [a]

    # raw JSON is kept, and an update only adds to the index
    await service.createOrUpdate(document("s1", b))
    got = await service.get("s1")
    assert got["unknown"] == {"kept": True}
    assert await files.keys("s1", "draft") == [a, b]
    assert [d["identifier"] for d in await service.list()] == ["s1"]

    await service.delete("s1")
    assert not await service.exists("s1")
    assert await files.keys("s1", "draft") == []
    assert sorted(deleted) == [a, b]


async def test_publish_copies_indexed_files(session, monkeypatch):
    copied = []

    async def fake_copy(pairs):
        copied.extend(pairs)

    async def fake_upload(*args, **kwargs):
        pass

    monkeypatch.setattr(study_module, "copy_objects", fake_copy)
    monkeypatch.setattr(s3_client, "upload_local_file", fake_upload)
    a = draft_key("s1", "a.csv")
    doc = await StudyDraftService(session).createOrUpdate(document("s1", a))
    await StudyService(session).save(StudyDraft.model_validate(doc))

    pub = a.replace("/draft/", "/pub/")
    assert copied == [(a, pub)]
    assert await StudyFileService(session).keys("s1", "pub") == [pub]


async def test_api_drafts_are_not_validated(client):
    body = {"identifier": "s2", "start_year": "not a year", "buildings": "?"}
    res = await client.post("/contribute/study-draft", json=body)
    assert res.status_code == 200, res.text
    res = await client.post("/contribute/study-draft", json=body)
    assert res.status_code == 409
    res = await client.get("/contribute/study-draft/s2")
    assert res.json()["start_year"] == "not a year"
    res = await client.put("/contribute/study-draft/other", json=body)
    assert res.status_code == 400
    res = await client.get("/contribute/study-draft/missing")
    assert res.status_code == 404


async def test_import_reads_drafts_and_files(monkeypatch):
    root = s3_client.to_s3_key("")
    keys = {
        "draft/": ["draft/s1/study.json", "draft/s1/files/D1/a.csv"],
        "pub/": ["pub/s2/study.json", "pub/s2/files/D1/b.csv"],
    }

    async def list_files(folder):
        return [root + key for key in keys[folder]]

    async def get_file(key):
        return json.dumps({"identifier": "wrong", "name": "A"}), "application/json"

    async def close():
        pass

    monkeypatch.setattr(s3_client, "list_files", list_files)
    monkeypatch.setattr(s3_client, "get_file", get_file)
    monkeypatch.setattr(s3_client, "close", close)
    drafts, files = await import_s3_drafts.read_s3()
    assert drafts == [
        {"identifier": "s1", "document": {"identifier": "s1", "name": "A"}}
    ]
    assert files == [
        {
            "key": root + "draft/s1/files/D1/a.csv",
            "study_identifier": "s1",
            "area": "draft",
        },
        {
            "key": root + "pub/s2/files/D1/b.csv",
            "study_identifier": "s2",
            "area": "pub",
        },
    ]


async def test_find_bundles_filters_pages_and_sorts(session):
    service = StudyDraftService(session)
    contributions = ContributionService(session)
    for identifier, name, contributor in [
        ("s1", "Alpha", {"name": "Ann Lee", "email": "ann@x.org"}),
        ("s2", "Beta 100%", {"name": "Bob", "email": "bob@y.org"}),
        ("s3", "Gamma", None),
    ]:
        doc = {"identifier": identifier, "name": name}
        if contributor:
            doc["contributors"] = [contributor]
        await service.createOrUpdate(doc)
        await contributions.touch_by_identifier(identifier)
    await contributions.publish_by_identifier("s2")

    async def ids(**kwargs):
        args = {"q": None, "published": None, "sort": "identifier", "desc": False}
        res = await service.find_bundles(**{**args, **kwargs}, skip=0, limit=10)
        return [bundle.study["identifier"] for bundle in res.data]

    assert await ids() == ["s1", "s2", "s3"]
    assert await ids(q="S3") == ["s3"]  # identifier
    assert await ids(q="100%") == ["s2"]  # name, escaped
    assert await ids(q="ann lee") == ["s1"]  # contributor name
    assert await ids(q="y.org") == ["s2"]  # contributor email
    assert await ids(published=True) == ["s2"]
    assert await ids(published=False) == ["s1", "s3"]
    assert await ids(sort="name", desc=True) == ["s3", "s2", "s1"]
    assert (await ids(sort="published_at", desc=True))[0] == "s2"

    page = await service.find_bundles(None, None, "identifier", False, 1, 1)
    assert page.total == 3
    assert [bundle.study["identifier"] for bundle in page.data] == ["s2"]
    assert page.data[0].contribution.published_at is not None
