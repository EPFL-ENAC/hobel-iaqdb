"""Explore downloads: the raw measurements of a selection, zipped with the
catalog of their studies, built in the background and delivered by email.

Several backend pods share the work through Postgres session-level advisory
locks held on the job's connection: one lock per job (exclusivity) and one
of DOWNLOAD_MAX_CONCURRENT slot locks (cluster-wide concurrency). A dead pod
drops its connection, which releases its locks, so its job is picked up again
by the next poll of any pod. Studies under data embargo are never exported."""

import asyncio
import hashlib
import logging
import re
import secrets
import smtplib
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

from api.config import config
from api.models.catalog import Building, Dataset, Instrument, Space, Study
from api.models.download import (
    DownloadEstimate,
    DownloadForm,
    DownloadRequest,
    DownloadRequestRead,
    DownloadRequestsResult,
    DownloadSelection,
)
from api.models.explore import ExploreQuery
from api.models.measurement import DatasetParameter, Parameter
from api.services.explore.envelope import check_parameters
from api.services.explore.facts import Fact
from api.services.explore.filters import apply_criteria, criteria_of, parse_filter
from api.services.s3 import s3_client
from fastapi import HTTPException
from sqlalchemy import func, or_, text
from sqlalchemy.dialects.postgresql import asyncpg as pg_dialect
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

log = logging.getLogger(__name__)

LINK_VALIDITY = timedelta(days=7)
POLL_SECONDS = 30
# a job whose pod died this many times is given up
MAX_ATTEMPTS = 3
# rate limits, per email and per client IP
MAX_ACTIVE = 2
MAX_DAILY = 10
# advisory lock namespaces (pg_try_advisory_lock(int, int))
JOB_NS, SLOT_NS = 0x1A0D, 0x1A0E
S3_FOLDER = "downloads"
UPLOAD_PART_SIZE = 64 << 20

EMBARGOED_STUDIES = text(
    """
    SELECT s.id FROM study s
    JOIN contribution c ON c.study_identifier = s.identifier
    WHERE coalesce(c.published_at, now()) + CASE c.data_embargo
            WHEN '3m' THEN INTERVAL '3 months'
            WHEN '6m' THEN INTERVAL '6 months'
            WHEN '1y' THEN INTERVAL '1 year'
          END > now()
    """
)

MEASUREMENT_HEADER = (
    "study,dataset,building,space,instrument,parameter,unit,data_type,"
    "timestamp,start_timestamp,end_timestamp,value,value_qualifier\n"
)

# catalog of the exported studies; contributor emails only when public
CATALOG_QUERIES = {
    "studies.csv": "SELECT * FROM study WHERE id = ANY($1::int[]) ORDER BY id",
    "contributors.csv": """
        SELECT p.id, s.identifier AS study, p.name, p.institution,
               CASE WHEN p.email_public THEN p.email END AS email
        FROM person p JOIN study s ON s.id = p.study_id
        WHERE p.study_id = ANY($1::int[]) ORDER BY p.id""",
    "buildings.csv": """
        SELECT s.identifier AS study, b.* FROM building b
        JOIN study s ON s.id = b.study_id
        WHERE b.study_id = ANY($1::int[]) ORDER BY b.id""",
    "certifications.csv": """
        SELECT b.identifier AS building, c.program, c.level FROM certification c
        JOIN building b ON b.id = c.building_id
        WHERE b.study_id = ANY($1::int[]) ORDER BY c.id""",
    "spaces.csv": """
        SELECT s.identifier AS study, b.identifier AS building, sp.*
        FROM space sp JOIN study s ON s.id = sp.study_id
        LEFT JOIN building b ON b.id = sp.building_id
        WHERE sp.study_id = ANY($1::int[]) ORDER BY sp.id""",
    "instruments.csv": """
        SELECT s.identifier AS study, i.* FROM instrument i
        JOIN study s ON s.id = i.study_id
        WHERE i.study_id = ANY($1::int[]) ORDER BY i.id""",
    "instrument_parameters.csv": """
        SELECT i.identifier AS instrument, ip.physical_parameter,
               ip.analysis_method, ip.measurement_uncertainty, ip.note
        FROM instrumentparameter ip JOIN instrument i ON i.id = ip.instrument_id
        WHERE i.study_id = ANY($1::int[]) ORDER BY ip.id""",
    "datasets.csv": """
        SELECT d.id, s.identifier AS study, d.name, d.description
        FROM dataset d JOIN study s ON s.id = d.study_id
        WHERE d.study_id = ANY($1::int[]) ORDER BY d.id""",
    "variables.csv": """
        SELECT v.dataset_id, d.name AS dataset, v.name, v.type, v.unit,
               v.format, v.reference
        FROM variable v JOIN dataset d ON d.id = v.dataset_id
        WHERE v.study_id = ANY($1::int[]) ORDER BY v.id""",
}


# ---- selection -------------------------------------------------------------


def explore_query(selection: DownloadSelection) -> ExploreQuery:
    return ExploreQuery(
        parameters=selection.parameters,
        **{"from": selection.from_},
        to=selection.to,
    )


async def embargoed_study_ids(session: AsyncSession) -> set[int]:
    return set((await session.exec(EMBARGOED_STUDIES)).scalars().all())


def datasets_statement(selection: DownloadSelection):
    """Datasets having records of the selection, with their study and an
    upper bound of their records (building and space criteria not applied)."""
    filter = parse_filter(selection.filter)
    dp = DatasetParameter
    statement = (
        select(
            col(Dataset.id).label("dataset_id"),
            col(Dataset.name).label("dataset"),
            col(Study.id).label("study_id"),
            col(Study.identifier).label("study"),
            func.sum(dp.n_records).label("n_records"),
        )
        .join(Dataset, col(Dataset.id) == col(dp.dataset_id))
        .join(Study, col(Study.id) == col(Dataset.study_id))
        .group_by(Dataset.id, Dataset.name, Study.id, Study.identifier)
        .order_by(Study.identifier, Dataset.id)
    )
    if selection.parameters:
        statement = statement.where(col(dp.parameter).in_(selection.parameters))
    if selection.from_:
        statement = statement.where(col(dp.last_at) >= selection.from_)
    if selection.to:
        statement = statement.where(col(dp.first_at) < selection.to)
    criteria = criteria_of(filter)
    if "dataset" in criteria:
        statement = apply_criteria(statement, Dataset, criteria["dataset"])
    if "study" in criteria:
        statement = apply_criteria(statement, Study, criteria["study"])
    return statement


async def estimate(
    session: AsyncSession, selection: DownloadSelection
) -> DownloadEstimate:
    await check_parameters(session, selection.parameters)
    embargoed = await embargoed_study_ids(session)
    rows = (await session.exec(datasets_statement(selection))).all()
    kept = [r for r in rows if r.study_id not in embargoed]
    return DownloadEstimate(
        n_records=sum(int(r.n_records) for r in kept),
        n_datasets=len(kept),
        n_embargoed_studies=len({r.study_id for r in rows if r.study_id in embargoed}),
        max_records=config.DOWNLOAD_MAX_RECORDS,
    )


# ---- request ---------------------------------------------------------------


async def create_request(
    session: AsyncSession, form: DownloadForm, client_ip: str | None
) -> DownloadRequest:
    estimated = await estimate(session, form)
    if estimated.n_records == 0:
        raise HTTPException(status_code=422, detail="no data matches the selection")
    if estimated.n_records > estimated.max_records:
        raise HTTPException(
            status_code=422,
            detail=f"the selection covers up to {estimated.n_records} records,"
            f" above the limit of {estimated.max_records}: narrow it down",
        )
    await check_rate_limits(session, form.email, client_ip)
    request = DownloadRequest(
        email=form.email,
        title=form.title,
        description=form.description,
        query=form.model_dump(
            mode="json", by_alias=True, include={"filter", "parameters", "from_", "to"}
        ),
        n_records=estimated.n_records,
        client_ip=client_ip,
        created_at=datetime.now(timezone.utc),
    )
    session.add(request)
    await session.commit()
    return request


async def check_rate_limits(
    session: AsyncSession, email: str, client_ip: str | None
) -> None:
    active = ("pending", "running")
    r = DownloadRequest
    who = [func.lower(r.email) == email.lower()]
    if client_ip:
        who.append(col(r.client_ip) == client_ip)
    n_active = (
        await session.exec(
            select(func.count()).where(col(r.status).in_(active), or_(*who))
        )
    ).one()
    if n_active >= MAX_ACTIVE:
        raise HTTPException(
            status_code=429,
            detail="downloads are already being prepared for you,"
            " wait for their email before requesting another one",
        )
    since = datetime.now(timezone.utc) - timedelta(days=1)
    n_daily = (
        await session.exec(
            select(func.count()).where(
                func.lower(r.email) == email.lower(), col(r.created_at) >= since
            )
        )
    ).one()
    if n_daily >= MAX_DAILY:
        raise HTTPException(
            status_code=429, detail="too many downloads requested today"
        )


async def list_requests(
    session: AsyncSession, skip: int, limit: int
) -> DownloadRequestsResult:
    """Most recent first, for the admin page."""
    total = (await session.exec(select(func.count(DownloadRequest.id)))).one()
    statement = (
        select(DownloadRequest)
        .order_by(
            col(DownloadRequest.created_at).desc(), col(DownloadRequest.id).desc()
        )
        .offset(skip)
        .limit(limit)
    )
    rows = (await session.exec(statement)).all()
    return DownloadRequestsResult(
        total=total,
        skip=skip,
        limit=limit,
        data=[DownloadRequestRead.model_validate(r) for r in rows],
    )


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def find_by_token(session: AsyncSession, token: str) -> DownloadRequest | None:
    statement = select(DownloadRequest).where(
        DownloadRequest.token_hash == hash_token(token)
    )
    return (await session.exec(statement)).first()


# ---- jobs ------------------------------------------------------------------


async def claim_and_run(engine: AsyncEngine) -> bool:
    """Process one job (build, or notify) if a cluster-wide slot is free and
    a job is not locked by another pod. Returns whether one was processed."""
    async with engine.connect() as conn:
        pg = (await conn.get_raw_connection()).driver_connection
        try:
            if not await take_slot(pg):
                return False
            for request_id in await candidates(engine):
                if await pg.fetchval(
                    "SELECT pg_try_advisory_lock($1, $2)", JOB_NS, request_id
                ):
                    if await run_job(engine, pg, request_id):
                        return True
                    await pg.execute(
                        "SELECT pg_advisory_unlock($1, $2)", JOB_NS, request_id
                    )
            return False
        finally:
            # the connection goes back to the pool: never keep its locks
            await pg.execute("SELECT pg_advisory_unlock_all()")


async def take_slot(pg) -> bool:
    for slot in range(config.DOWNLOAD_MAX_CONCURRENT):
        if await pg.fetchval("SELECT pg_try_advisory_lock($1, $2)", SLOT_NS, slot):
            return True
    return False


async def candidates(engine: AsyncEngine) -> list[int]:
    """Jobs to build (pending, or running on a dead pod) or to notify."""
    r = DownloadRequest
    async with AsyncSession(engine) as session:
        statement = (
            select(r.id)
            .where(
                or_(
                    col(r.status).in_(("pending", "running")),
                    col(r.status).in_(("ready", "failed"))
                    & col(r.notified_at).is_(None),
                )
            )
            .order_by(r.created_at)
        )
        return list((await session.exec(statement)).all())


async def run_job(engine: AsyncEngine, pg, request_id: int) -> bool:
    """With the job lock held: build what is to build, notify what is to
    notify. Re-reads the row, which may have moved on since `candidates`."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        request = await session.get(DownloadRequest, request_id)
        if request is None or request.notified_at is not None:
            return False
        if request.status in ("pending", "running"):
            if request.attempts >= MAX_ATTEMPTS:
                request.status = "failed"
                request.error = f"interrupted {request.attempts} times"
            else:
                request.status = "running"
                request.attempts += 1
            session.add(request)
            await session.commit()
            if request.status == "running":
                await build(session, pg, request)
        await notify(session, request)
    return True


async def build(session: AsyncSession, pg, request: DownloadRequest) -> None:
    try:
        with tempfile.TemporaryDirectory(dir=config.DOWNLOAD_TMP_DIR or None) as tmp:
            path = Path(tmp) / "download.zip"
            n_records = await build_archive(pg, request, path)
            key = f"{S3_FOLDER}/{request.id}.zip"
            await upload_archive(path, key)
            request.size = path.stat().st_size
        request.status = "ready"
        request.n_records = n_records
        request.s3_key = key
        request.ready_at = datetime.now(timezone.utc)
    except Exception as e:
        log.exception("download %s failed", request.id)
        request.status = "failed"
        request.error = f"{type(e).__name__}: {e}"
    session.add(request)
    await session.commit()


async def notify(session: AsyncSession, request: DownloadRequest) -> None:
    """Email the outcome. The token only exists from here: a crash between
    build and notify leaves the job to the next poll, which sends the link.
    A failed send is retried by the next poll, a refused address is not."""
    now = datetime.now(timezone.utc)
    try:
        if request.status == "ready":
            token = secrets.token_urlsafe(32)
            # set even if the address is refused, so that the archive expires
            request.expires_at = now + LINK_VALIDITY
            await send_mail(
                request.email, *ready_email(request, token, request.expires_at)
            )
            request.token_hash = hash_token(token)
        else:
            await send_mail(request.email, *failed_email(request))
    except smtplib.SMTPRecipientsRefused:
        log.warning("download %s: address %s refused", request.id, request.email)
    request.notified_at = now
    session.add(request)
    await session.commit()


async def expire(engine: AsyncEngine) -> int:
    """Delete the archives past their link validity. Safe on every pod: the
    status update decides which pod deletes an object."""
    async with AsyncSession(engine) as session:
        keys = (
            (
                await session.exec(
                    text(
                        "UPDATE download_request SET status = 'expired'"
                        " WHERE status = 'ready' AND expires_at < now()"
                        " RETURNING s3_key"
                    )
                )
            )
            .scalars()
            .all()
        )
        await session.commit()
    for key in keys:
        try:
            await delete_archive(key)
        except Exception:
            # the bucket lifecycle rule on downloads/ is the backstop
            log.exception("could not delete %s", key)
    return len(keys)


async def poll(engine: AsyncEngine) -> None:
    """Run by every pod: pick up jobs left by dead pods, expire archives."""
    while True:
        try:
            while await claim_and_run(engine):
                pass
            await expire(engine)
        except Exception:
            log.exception("download poll failed")
        await asyncio.sleep(POLL_SECONDS)


# ---- archive ---------------------------------------------------------------


class LazyEntry:
    """A zip entry opened at the first chunk, so an empty export leaves no
    file. Compression runs in a thread, off the event loop."""

    def __init__(self, zf: zipfile.ZipFile, name: str, header: str):
        self.zf, self.name, self.header = zf, name, header
        self.entry = None

    async def write(self, data: bytes) -> None:
        if self.entry is None:
            self.entry = self.zf.open(self.name, "w", force_zip64=True)
            self.entry.write(self.header.encode())
        await asyncio.to_thread(self.entry.write, data)

    def close(self) -> None:
        if self.entry is not None:
            self.entry.close()


def compile_query(statement) -> tuple[str, list]:
    """SQLAlchemy statement -> asyncpg SQL with $n placeholders and args."""
    compiled = statement.compile(
        dialect=pg_dialect.dialect(), compile_kwargs={"render_postcompile": True}
    )
    return str(compiled), [compiled.params[name] for name in compiled.positiontup]


def measurement_statement(query: ExploreQuery, filter: dict, dataset_id: int):
    fact = Fact("raw")
    m = fact.table
    statement = (
        select(
            col(Study.identifier),
            col(Dataset.name),
            col(Building.identifier),
            col(Space.identifier),
            col(Instrument.identifier),
            m.c.parameter,
            col(Parameter.unit),
            m.c.data_type,
            m.c.ts,
            m.c.start_ts,
            m.c.end_ts,
            m.c.value,
            m.c.value_qualifier,
        )
        .select_from(
            m.join(Study, col(Study.id) == m.c.study_id)
            .join(Dataset, col(Dataset.id) == m.c.dataset_id)
            .join(Parameter, col(Parameter.slug) == m.c.parameter)
            .outerjoin(Building, col(Building.id) == m.c.building_id)
            .outerjoin(Space, col(Space.id) == m.c.space_id)
            .outerjoin(Instrument, col(Instrument.id) == m.c.instrument_id)
        )
        .where(m.c.dataset_id == dataset_id)
        # not `parameter, ts`: when its statistics make the planner consider
        # sorting inside compressed chunks, TimescaleDB fails to plan a sort
        # led by the varchar segmentby column ("missing operator
        # 1(1043,1043) in opfamily 1994"), even on an empty dataset
        .order_by(m.c.ts, m.c.parameter)
    )
    return fact.where(statement, query, filter, query.parameters)


def safe_name(value: str) -> str:
    return re.sub(r"[^\w.-]+", "_", value).strip("_") or "unnamed"


async def build_archive(pg, request: DownloadRequest, path: Path) -> int:
    """Write the zip of the request; returns the exported record count. One
    read-only snapshot: a publish meanwhile cannot mix two catalog states."""
    selection = DownloadSelection.model_validate(request.query)
    query = explore_query(selection)
    filter = parse_filter(selection.filter)
    async with pg.transaction(isolation="repeatable_read", readonly=True):
        datasets, embargoed = await snapshot_datasets(pg, selection)
        counts: dict[str, int] = {}
        study_ids: set[int] = set()
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            for d in datasets:
                name = (
                    f"measurements/{safe_name(d['study'])}/"
                    f"{d['dataset_id']}_{safe_name(d['dataset'])}.csv"
                )
                sql, args = compile_query(
                    measurement_statement(query, filter, d["dataset_id"])
                )
                entry = LazyEntry(zf, name, MEASUREMENT_HEADER)
                try:
                    status = await pg.copy_from_query(
                        sql, *args, output=entry.write, format="csv"
                    )
                finally:
                    entry.close()
                n = int(status.split()[-1])
                if n:
                    counts[name] = n
                    study_ids.add(d["study_id"])
            await write_catalog(pg, zf, sorted(study_ids), selection.parameters)
            content = await readme(
                pg, request, selection, counts, sorted(study_ids), embargoed
            )
            zf.writestr("README.md", content)
    return sum(counts.values())


async def snapshot_datasets(pg, selection: DownloadSelection):
    """The selection's datasets minus embargoed studies, read in the job
    snapshot. Returns (datasets, embargoed study identifiers left out)."""
    sql, args = compile_query(datasets_statement(selection))
    rows = await pg.fetch(sql, *args)
    embargoed = {r["id"] for r in await pg.fetch(str(EMBARGOED_STUDIES))}
    kept = [r for r in rows if r["study_id"] not in embargoed]
    excluded = sorted({r["study"] for r in rows if r["study_id"] in embargoed})
    return kept, excluded


async def write_catalog(
    pg, zf: zipfile.ZipFile, study_ids: list[int], parameters: list[str]
) -> None:
    for name, sql in CATALOG_QUERIES.items():
        await copy_entry(pg, zf, f"catalog/{name}", sql, study_ids)
    params_sql = (
        "SELECT slug, label, reference, unit FROM parameter"
        + (" WHERE slug = ANY($1::text[])" if parameters else "")
        + " ORDER BY slug"
    )
    await copy_entry(
        pg,
        zf,
        "catalog/parameters.csv",
        params_sql,
        *([parameters] if parameters else []),
    )


async def copy_entry(pg, zf: zipfile.ZipFile, name: str, sql: str, *args) -> None:
    with zf.open(name, "w") as entry:

        async def write(data: bytes) -> None:
            entry.write(data)

        await pg.copy_from_query(sql, *args, output=write, format="csv", header=True)


async def readme(
    pg,
    request: DownloadRequest,
    selection: DownloadSelection,
    counts: dict[str, int],
    study_ids: list[int],
    embargoed: list[str],
) -> str:
    studies = await pg.fetch(
        "SELECT identifier, name, license, citation, doi FROM study"
        " WHERE id = ANY($1::int[]) ORDER BY identifier",
        study_ids,
    )
    lines = [
        f"# {request.title}",
        "",
        request.description,
        "",
        f"Requested on {request.created_at:%Y-%m-%d %H:%M} UTC from the IAQ"
        " database Explore page.",
        "",
        "## Selection",
        "",
        f"- Parameters: {', '.join(selection.parameters) or 'all'}",
        f"- From: {selection.from_ or '-'}",
        f"- To (excluded): {selection.to or '-'}",
        f"- Filter: `{selection.filter or '{}'}`",
        "",
        "## Files",
        "",
        "- `measurements/<study>/<dataset>.csv`: one row per reading, values in"
        " the canonical unit of their parameter; timestamps are the local wall"
        " clock time of the measurement.",
        "- `catalog/`: studies, contributors, buildings, spaces, instruments,"
        " datasets, variables and parameters of the exported studies.",
        "",
        "| File | Records |",
        "|---|---|",
        *[f"| `{name}` | {n} |" for name, n in sorted(counts.items())],
        "",
        "## Studies, licenses and citations",
        "",
        "Cite each study whose data you use.",
        "",
    ]
    for s in studies:
        lines += [
            f"### {s['name'] or s['identifier']} (`{s['identifier']}`)",
            "",
            f"- License: {s['license'] or '-'}",
            f"- Citation: {s['citation'] or '-'}",
            f"- DOI: {s['doi'] or '-'}",
            "",
        ]
    if embargoed:
        lines += [
            "## Excluded studies",
            "",
            "These studies match the selection but are under data embargo:"
            " their measurements cannot be downloaded yet.",
            "",
            *[f"- `{identifier}`" for identifier in embargoed],
            "",
        ]
    return "\n".join(lines)


# ---- storage and mail ------------------------------------------------------


async def upload_archive(path: Path, key: str) -> None:
    """Private multipart upload: the object is only reachable through the
    token route, never public-read."""
    full_key = s3_client.to_s3_path(key)
    bucket = s3_client.bucket
    async with s3_client._client() as client:
        upload = await client.create_multipart_upload(
            Bucket=bucket, Key=full_key, ContentType="application/zip"
        )
        upload_id = upload["UploadId"]
        try:
            parts = []
            with path.open("rb") as stream:
                number = 1
                while chunk := await asyncio.to_thread(stream.read, UPLOAD_PART_SIZE):
                    part = await client.upload_part(
                        Bucket=bucket,
                        Key=full_key,
                        UploadId=upload_id,
                        PartNumber=number,
                        Body=chunk,
                    )
                    parts.append({"PartNumber": number, "ETag": part["ETag"]})
                    number += 1
            await client.complete_multipart_upload(
                Bucket=bucket,
                Key=full_key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
        except BaseException:
            await client.abort_multipart_upload(
                Bucket=bucket, Key=full_key, UploadId=upload_id
            )
            raise


async def stream_archive(key: str):
    async with s3_client._client() as client:
        response = await client.get_object(
            Bucket=s3_client.bucket, Key=s3_client.to_s3_path(key)
        )
        async for chunk in response["Body"].iter_chunks(1 << 20):
            yield chunk


async def delete_archive(key: str) -> None:
    await s3_client.delete_file(s3_client.to_s3_path(key))


def download_url(token: str) -> str:
    return f"{config.APP_URL.rstrip('/')}{config.PATH_PREFIX}/downloads/{token}"


def ready_email(
    request: DownloadRequest, token: str, expires_at: datetime
) -> tuple[str, str]:
    size_mb = (request.size or 0) / (1 << 20)
    return (
        f"Your IAQ data download is ready: {request.title}",
        f"""Hello,

The data you requested from the IAQ database Explore page is ready.

  {request.title}
  {request.description}

Records: {request.n_records}
Size: {size_mb:.1f} MB

Download it from this link, valid until {expires_at:%Y-%m-%d %H:%M} UTC:

  {download_url(token)}

The archive README lists the license and citation of each study: please
cite the studies whose data you use.
""",
    )


def failed_email(request: DownloadRequest) -> tuple[str, str]:
    return (
        f"Your IAQ data download failed: {request.title}",
        f"""Hello,

The data you requested from the IAQ database Explore page could not be
prepared:

  {request.title}

Please try again later, or narrow down the selection.
""",
    )


async def send_mail(to: str, subject: str, body: str) -> None:
    if not config.SMTP_HOST:
        log.warning(
            "SMTP_HOST not set, email to %s not sent:\n%s\n%s", to, subject, body
        )
        return
    message = EmailMessage()
    message["From"] = config.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    await asyncio.to_thread(_send, message)


def _send(message: EmailMessage) -> None:
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as smtp:
        if config.SMTP_STARTTLS:
            smtp.starttls()
        if config.SMTP_USER:
            smtp.login(config.SMTP_USER, config.SMTP_PASSWORD or "")
        smtp.send_message(message)
