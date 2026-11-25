"""Access control of the S3 files routes and of the moves of uploads."""

import uuid
from datetime import datetime

import pytest
from aiobotocore.response import StreamingBody
from api.auth import kc_service
from api.models.catalog import Contribution, Study, StudyDraft, StudyFile
from api.services import s3 as s3_module
from api.services import study_draft as draft_module
from api.services.s3 import s3_client, tmp_key
from api.services.study_draft import StudyDraftService
from api.views import contribute as contribute_view
from api.views import files as files_view

PREFIX = s3_client.path_prefix
STORED = [
    "downloads/12.zip",
    "pub/s1/files/D1/a.csv",
    "pub/s1/study.json",
    "draft/s1/files/tmp/a.csv",
]


def stub_s3(monkeypatch, content, content_type):
    async def head_object(_):
        return {"ContentType": content_type, "ContentLength": len(content)}

    async def stream_object(_):
        yield content

    monkeypatch.setattr(files_view, "head_object", head_object)
    monkeypatch.setattr(files_view, "stream_object", stream_object)


@pytest.mark.parametrize("path", [*STORED, f"{PREFIX}tmp/1/a.csv"])
async def test_get_file_refuses_anonymous(client, monkeypatch, path):
    async def head_object(_):
        raise AssertionError("S3 was read")

    monkeypatch.setattr(files_view, "head_object", head_object)
    assert (await client.get(f"/files/{path}")).status_code == 403


@pytest.mark.parametrize(
    "roles, status", [(["admin"], 200), (["contributor"], 403), ([], 403)]
)
async def test_get_file_is_for_admins(client, monkeypatch, roles, status):
    def decode(_):
        return {
            "sub": "1",
            "preferred_username": "u",
            "email": "u@example.org",
            "given_name": "U",
            "family_name": "U",
            "realm_access": {"roles": roles},
            "resource_access": {kc_service.client_id: {"roles": roles}},
        }

    stub_s3(monkeypatch, b"<script>", "text/html")
    monkeypatch.setattr(kc_service.keycloak_openid, "decode_token", decode)
    res = await client.get(
        "/files/draft/s1/files/D1/été.html", headers={"Authorization": "Bearer x"}
    )
    assert res.status_code == status
    if status == 200:
        assert res.content == b"<script>"
        assert res.headers["content-length"] == "8"
        assert res.headers["content-disposition"].startswith("attachment;")
        assert res.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize(
    "path, key",
    [
        ("tmp/1/a.csv", f"{PREFIX}tmp/1/a.csv"),
        (f"{PREFIX}tmp/1/a.csv", f"{PREFIX}tmp/1/a.csv"),
        (f"{PREFIX}tmp/1/a%20b.csv", f"{PREFIX}tmp/1/a b.csv"),
        *((path, None) for path in STORED),
        (f"{PREFIX}pub/s1/files/tmp/a.csv", None),
        ("tmp/../pub/s1/study.json", None),
        ("tmp/%2E%2E/pub/s1/study.json", None),
        ("", None),
    ],
)
def test_tmp_key(path, key):
    assert tmp_key(path) == key


async def test_delete_file_only_deletes_uploads(client, monkeypatch):
    deleted = []

    async def delete_objects(keys):
        deleted.extend(keys)

    monkeypatch.setattr(files_view, "delete_objects", delete_objects)
    for path in [*STORED, "pub/s1/files/tmp/a.csv", f"{PREFIX}tmp/1/a.csv"]:
        assert (await client.delete(f"/files/{path}")).status_code == 204
    assert deleted == [f"{PREFIX}tmp/1/a.csv"]


async def test_draft_only_moves_uploads(session, monkeypatch):
    copied, deleted = [], []

    async def copy_object(source, destination):
        copied.append((source, destination))

    async def delete_objects(keys):
        deleted.extend(keys)

    monkeypatch.setattr(draft_module, "copy_object", copy_object)
    monkeypatch.setattr(draft_module, "delete_objects", delete_objects)
    upload = f"{PREFIX}tmp/1/a%20b.csv"
    stolen = f"{PREFIX}draft/victim/files/tmp/c.csv"
    children = [{"name": p.split("/")[-1], "path": p} for p in (upload, stolen)]
    children[0]["name"] = "a b.csv"
    document = StudyDraft(
        identifier="s1",
        datasets=[{"name": "D1", "description": "", "folder": {"children": children}}],
    ).model_dump(mode="json")
    saved = await StudyDraftService(session).createOrUpdate(document)

    key = f"{PREFIX}draft/s1/files/D1/a b.csv"
    assert copied == [(f"{PREFIX}tmp/1/a b.csv", key)]
    assert deleted == [f"{PREFIX}tmp/1/a b.csv"]
    files = saved["datasets"][0]["folder"]["children"]
    assert files[0]["path"] == key.replace(" ", "%20")
    assert await StudyDraftService(session).files.keys("s1", "draft") == [key]


async def test_copies_are_private(monkeypatch):
    calls = []

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def head_object(self, **_):
            return {"ContentLength": 1}

        async def copy_object(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(s3_client, "_client", Client)
    await s3_module.copy_object("a", "b")
    assert calls[0]["Key"] == "b" and "ACL" not in calls[0]


async def add_draft(session, identifier, **contribution):
    key = f"{PREFIX}draft/{identifier}/files/D1/a b.csv"
    session.add(StudyFile(key=key, study_identifier=identifier, area="draft"))
    now = datetime.now()
    session.add(
        Contribution(
            study_identifier=identifier, created_at=now, updated_at=now, **contribution
        )
    )
    await session.commit()
    return key.replace(" ", "%20")


async def get_anonymously(client, monkeypatch, path):
    stub_s3(monkeypatch, b"1,2", "text/csv")
    return (await client.get(f"/files/{path}")).status_code


async def test_contributor_reads_open_draft(session, client, monkeypatch):
    path = await add_draft(session, str(uuid.uuid4()))
    assert await get_anonymously(client, monkeypatch, path) == 200
    # a file that the draft does not have
    other = path.replace("a%20b", "c")
    assert await get_anonymously(client, monkeypatch, other) == 403


async def test_contributor_reads_own_upload(client, monkeypatch):
    path = f"{PREFIX}tmp/{uuid.uuid4().hex}/a.csv"
    assert await get_anonymously(client, monkeypatch, path) == 200
    # former folders, named after the time
    path = f"{PREFIX}tmp/1764000000123456/a.csv"
    assert await get_anonymously(client, monkeypatch, path) == 403


async def test_published_draft_is_not_public(session, client, monkeypatch):
    path = await add_draft(session, str(uuid.uuid4()), published_at=datetime.now())
    assert await get_anonymously(client, monkeypatch, path) == 403
    # in the catalog, contribution not marked yet
    identifier = str(uuid.uuid4())
    path = await add_draft(session, identifier)
    session.add(Study(identifier=identifier))
    await session.commit()
    assert await get_anonymously(client, monkeypatch, path) == 403
    # guessable identifier
    path = await add_draft(session, "study-a")
    assert await get_anonymously(client, monkeypatch, path) == 403
    # escape from the folder
    identifier = str(uuid.uuid4())
    key = f"{PREFIX}draft/{identifier}/../../pub/s1/study.json"
    session.add(StudyFile(key=key, study_identifier=identifier, area="draft"))
    await session.commit()
    path = key.replace("..", "%252E%252E")
    assert await get_anonymously(client, monkeypatch, path) == 403


async def test_draft_identifiers_are_not_listed(session, client):
    identifier = str(uuid.uuid4())
    await add_draft(session, identifier, created_by="someone")
    assert (await client.get("/contribute/contributions")).status_code == 401
    assert (await client.get("/contribute/contribution/1")).status_code == 404
    body = {"data_embargo": "3m"}
    res = await client.put("/contribute/contribution/1", json=body)
    assert res.status_code == 404
    res = await client.put(f"/contribute/contribution/{identifier}", json=body)
    assert res.status_code == 200 and res.json()["data_embargo"] == "3m"
    # the form shows the stored embargo, without the user names
    res = await client.get(f"/contribute/contribution/{identifier}")
    assert res.json() == {
        "study_identifier": identifier,
        "data_embargo": "3m",
        "published_at": None,
    }


@pytest.mark.parametrize("mark", ["contribution", "study"])
async def test_published_study_is_locked(session, client, monkeypatch, mark):
    identifier = str(uuid.uuid4())
    published = {"published_at": datetime.now()} if mark == "contribution" else {}
    await add_draft(session, identifier, data_embargo="1y", **published)
    if mark == "study":
        session.add(Study(identifier=identifier))
        await session.commit()
    draft = {"identifier": identifier, "name": "changed"}
    writes = [
        ("PUT", f"/contribute/study-draft/{identifier}", draft),
        ("POST", "/contribute/study-draft", draft),
        ("PUT", f"/contribute/contribution/{identifier}", {"data_embargo": "none"}),
    ]
    for method, path, body in writes:
        res = await client.request(method, path, json=body)
        assert res.status_code == 403, path
        assert "published" in res.json()["detail"]
    assert not await StudyDraftService(session).exists(identifier)
    res = await client.get(f"/contribute/contribution/{identifier}")
    assert res.json()["data_embargo"] == "1y"

    # admins still can
    monkeypatch.setattr(contribute_view, "is_admin", lambda user: True)

    async def delete_objects(_):
        pass

    monkeypatch.setattr(draft_module, "delete_objects", delete_objects)
    for method, path, body in (writes[0], writes[2]):
        assert (await client.request(method, path, json=body)).status_code == 200
    res = await client.get(f"/contribute/contribution/{identifier}")
    assert res.json()["data_embargo"] == "none"


async def test_open_draft_is_editable(session, client):
    identifier = str(uuid.uuid4())
    draft = {"identifier": identifier, "name": "a"}
    path = f"/contribute/study-draft/{identifier}"
    assert (await client.put(path, json=draft)).status_code == 200
    assert (await client.put(path, json=draft)).status_code == 200


async def test_missing_file(client, monkeypatch):
    async def head_object(_):
        return None

    monkeypatch.setattr(files_view, "head_object", head_object)
    path = f"{PREFIX}tmp/{uuid.uuid4().hex}/a.csv"
    assert (await client.get(f"/files/{path}")).status_code == 404


async def test_stream_object(monkeypatch):
    class Raw:
        """The aiohttp response that StreamingBody wraps."""

        closed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            Raw.closed = True

    class Content:
        chunks = [b"1,", b"2"]

        async def read(self, _):
            return self.chunks.pop(0) if self.chunks else b""

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def get_object(self, **_):
            raw = Raw()
            raw.content = Content()
            return {"Body": StreamingBody(raw, "3")}

    monkeypatch.setattr(s3_client, "_client", Client)
    assert [c async for c in s3_module.stream_object("a")] == [b"1,", b"2"]
    assert Raw.closed
