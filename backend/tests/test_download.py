import asyncio
import csv
import io
import re
import smtplib
import zipfile
from datetime import datetime, timedelta, timezone

import pytest
from api.config import config
from api.models.catalog import Contribution
from api.models.download import DownloadForm, DownloadRequest
from api.services import download
from tests.expected import series_of
from tests.test_stats_metadata import loaded_fixture

FORM = {
    "email": "someone@example.org",
    "title": "CO2 in offices",
    "description": "For a comparison with our own data",
}


@pytest.fixture
def storage(monkeypatch, tmp_path):
    """S3 and SMTP stand-ins: archives kept in memory, emails recorded."""
    archives: dict[str, bytes] = {}
    mails: list[tuple[str, str, str]] = []

    async def upload_archive(path, key):
        await asyncio.sleep(0.1)  # leaves room for a concurrent claim
        archives[key] = path.read_bytes()

    async def stream_archive(key):
        yield archives[key]

    async def send_mail(to, subject, body):
        mails.append((to, subject, body))

    monkeypatch.setattr(download, "upload_archive", upload_archive)
    monkeypatch.setattr(download, "send_mail", send_mail)
    monkeypatch.setattr(download, "stream_archive", stream_archive)
    monkeypatch.setattr("api.views.download.stream_archive", stream_archive)
    return archives, mails


def token_of(body: str) -> str:
    return re.search(r"/downloads/(\S+)", body).group(1)


async def embargo(session, months: str = "1y", published_days_ago: int = 0):
    # contribution timestamps are naive, as the publish route writes them
    published_at = datetime.now() - timedelta(days=published_days_ago)
    session.add(
        Contribution(
            study_identifier="study-a",
            data_embargo=months,
            created_at=published_at,
            updated_at=published_at,
            published_at=published_at,
        )
    )
    await session.commit()


async def test_estimate_and_embargo(client, session, clean_db, tmp_path, storage):
    fx = await loaded_fixture(session, clean_db, tmp_path)
    response = await client.post("/downloads/estimate", json={"parameters": ["co2"]})
    assert response.status_code == 200, response.text
    expected = sum(len(p) for p in series_of(fx, "co2"))
    assert response.json() == {
        "n_records": expected,
        "n_datasets": 1,
        "n_embargoed_studies": 0,
        "max_records": config.DOWNLOAD_MAX_RECORDS,
    }
    await embargo(session)
    response = await client.post("/downloads/estimate", json={})
    assert response.json()["n_records"] == 0
    assert response.json()["n_embargoed_studies"] == 1
    response = await client.post("/downloads", json=FORM)
    assert response.status_code == 422


async def test_expired_embargo_is_downloadable(client, session, clean_db, tmp_path):
    await loaded_fixture(session, clean_db, tmp_path)
    await embargo(session, "3m", published_days_ago=100)
    response = await client.post("/downloads/estimate", json={})
    assert response.json()["n_embargoed_studies"] == 0
    assert response.json()["n_datasets"] == 2


async def test_request_build_and_download(client, session, clean_db, tmp_path, storage):
    archives, mails = storage
    fx = await loaded_fixture(session, clean_db, tmp_path)
    response = await client.post(
        "/downloads",
        json={
            **FORM,
            "parameters": ["co2"],
            "filter": '{"$building": {"country": "CH"}}',
        },
    )
    assert response.status_code == 202, response.text
    # the background task ran within the request
    assert len(mails) == 1
    to, subject, body = mails[0]
    assert to == FORM["email"] and FORM["title"] in subject
    response = await client.get(f"/downloads/{token_of(body)}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "CO2_in_offices.zip" in response.headers["content-disposition"]
    zf = zipfile.ZipFile(io.BytesIO(response.content))
    names = zf.namelist()
    assert names[0] == "measurements/study-a/1_D1.csv"
    assert not any("D2" in n for n in names)
    rows = list(csv.DictReader(io.TextIOWrapper(zf.open(names[0]), "utf-8")))
    assert len(rows) == sum(len(p) for p in series_of(fx, "co2"))
    assert {r["parameter"] for r in rows} == {"co2"}
    assert {r["unit"] for r in rows} == {"ppm"}
    assert {r["space"] for r in rows} == {"S1", "S2", ""}
    assert "catalog/buildings.csv" in names and "catalog/parameters.csv" in names
    readme = zf.read("README.md").decode()
    assert f"| `{names[0]}` | {len(rows)} |" in readme
    assert "study-a" in readme and "Excluded studies" not in readme
    contributors = zf.read("catalog/contributors.csv").decode()
    assert contributors.startswith("id,study,name,institution,email")

    request = (await session.exec(DownloadRequest.__table__.select())).one()
    assert request.status == "ready" and request.n_records == len(rows)
    await session.exec(
        DownloadRequest.__table__.update().values(
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)
        )
    )
    await session.commit()
    response = await client.get(f"/downloads/{token_of(body)}")
    assert response.status_code == 410
    assert await download.expire(clean_db) == 1
    assert (await client.get("/downloads/unknown")).status_code == 404


async def test_one_run_for_concurrent_claims(session, clean_db, tmp_path, storage):
    archives, mails = storage
    await loaded_fixture(session, clean_db, tmp_path)
    # left `running` by a dead pod: nobody holds its lock
    session.add(
        DownloadRequest(
            email=FORM["email"],
            title="orphan",
            description="d",
            query={"parameters": ["pm2_5"]},
            status="running",
            attempts=1,
            n_records=1,
            created_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()
    results = await asyncio.gather(
        download.claim_and_run(clean_db), download.claim_and_run(clean_db)
    )
    assert sorted(results) == [False, True]
    assert len(archives) == 1 and len(mails) == 1
    assert await download.claim_and_run(clean_db) is False


async def test_limits(client, session, clean_db, tmp_path, storage, monkeypatch):
    await loaded_fixture(session, clean_db, tmp_path)
    monkeypatch.setattr(config, "DOWNLOAD_MAX_RECORDS", 10)
    response = await client.post("/downloads", json=FORM)
    assert response.status_code == 422
    assert "above the limit of 10" in response.text
    monkeypatch.undo()
    for _ in range(download.MAX_ACTIVE):
        session.add(
            DownloadRequest(
                email=FORM["email"].upper(),
                title="t",
                description="d",
                query={},
                n_records=1,
                created_at=datetime.now(timezone.utc),
            )
        )
    await session.commit()
    response = await client.post("/downloads", json=FORM)
    assert response.status_code == 429
    response = await client.post("/downloads", json={**FORM, "email": "nope"})
    assert response.status_code == 422


async def test_list_requests(client, session, clean_db):
    for i in range(3):
        session.add(
            DownloadRequest(
                email=FORM["email"],
                title=f"t{i}",
                description="d",
                query={},
                n_records=i,
                token_hash="secret" if i == 0 else None,
                created_at=datetime.now(timezone.utc) + timedelta(minutes=i),
            )
        )
    await session.commit()
    result = await download.list_requests(session, skip=1, limit=1)
    assert result.total == 3
    assert [r.title for r in result.data] == ["t1"]
    assert "token_hash" not in result.data[0].model_dump()
    # admins only
    assert (await client.get("/downloads")).status_code in (401, 403)


async def test_all_parameters_and_from(session, clean_db, tmp_path, storage):
    """`from` survives the request round trip; no parameter filter exports
    them all (the ordering bug it once hit needs production planner
    statistics, see measurement_statement)."""
    archives, mails = storage
    fx = await loaded_fixture(session, clean_db, tmp_path)
    form = DownloadForm.model_validate({**FORM, "from": "2023-03-03"})
    assert form.from_ is not None
    request = await download.create_request(session, form, None)
    assert request.query["from"] == "2023-03-03"
    assert await download.claim_and_run(clean_db) is True
    await session.refresh(request)
    assert request.status == "ready", request.error
    expected = sum(
        1
        for slug in ("co2", "air_temperature", "pm2_5")
        for p in series_of(fx, slug)
        for t, _ in p
        if t >= datetime(2023, 3, 3)
    )
    assert request.n_records == expected


def ready_job(title: str) -> DownloadRequest:
    return DownloadRequest(
        email=FORM["email"],
        title=title,
        description="d",
        query={},
        status="ready",
        n_records=1,
        size=1,
        s3_key=f"downloads/{title}.zip",
        created_at=datetime.now(timezone.utc),
    )


async def test_failed_email_holds_up_no_other_job(
    session, clean_db, storage, monkeypatch
):
    archives, mails = storage
    for title in ("down", "bad", "fine"):
        session.add(ready_job(title))
    await session.commit()

    async def send_mail(to, subject, body):
        if subject.endswith(": down"):
            raise smtplib.SMTPServerDisconnected("relay down")
        if subject.endswith(": bad"):
            raise ValueError("unencodable header")
        mails.append((to, subject, body))

    monkeypatch.setattr(download, "send_mail", send_mail)
    while await download.claim_and_run(clean_db):
        pass
    assert [subject for _, subject, _ in mails] == [
        "Your IAQ data download is ready: fine"
    ]
    rows = {
        r.title: r for r in (await session.exec(DownloadRequest.__table__.select()))
    }
    # transient: retried by the next poll; permanent: given up, with the reason
    assert rows["down"].notified_at is None
    assert rows["bad"].notified_at is not None and "ValueError" in rows["bad"].error
    assert rows["bad"].token_hash is None


async def test_unicode_title_download(client, session, clean_db, storage):
    archives, mails = storage
    session.add(ready_job("Données CO₂ 北京"))
    await session.commit()
    archives["downloads/Données CO₂ 北京.zip"] = b"zip"
    assert await download.claim_and_run(clean_db) is True
    response = await client.get(f"/downloads/{token_of(mails[0][2])}")
    assert response.status_code == 200, response.text
    disposition = response.headers["content-disposition"]
    assert 'filename="Donn_es_CO.zip"' in disposition
    assert (
        "filename*=UTF-8''Donn%C3%A9es_CO%E2%82%82_%E5%8C%97%E4%BA%AC.zip"
        in disposition
    )


@pytest.mark.parametrize(
    "field,value",
    [("email", "a\nb@example.org"), ("title", "CO2\nBcc: x@example.org")],
)
def test_form_rejects_line_breaks(field, value):
    with pytest.raises(ValueError):
        DownloadForm.model_validate({**FORM, field: value})


async def test_queue_cap(client, session, clean_db, tmp_path, storage, monkeypatch):
    await loaded_fixture(session, clean_db, tmp_path)
    monkeypatch.setattr(download, "MAX_QUEUED", 1)
    session.add(
        DownloadRequest(
            email="other@example.org",
            title="t",
            description="d",
            query={},
            n_records=1,
            client_ip="10.0.0.9",
            created_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()
    response = await client.post("/downloads", json=FORM)
    assert response.status_code == 429
    assert "try again later" in response.text
