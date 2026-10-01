"""Download of the raw measurements matching an Explore selection: estimate,
request (built in the background, link sent by email), then the link."""

import re
from datetime import datetime, timezone
from urllib.parse import quote

from api.auth import User, kc_service
from api.db import get_engine, get_session
from api.models.download import (
    DownloadAccepted,
    DownloadEstimate,
    DownloadForm,
    DownloadRequestsResult,
    DownloadSelection,
)
from api.services.download import (
    claim_and_run,
    create_request,
    estimate,
    find_by_token,
    list_requests,
    safe_name,
    stream_archive,
)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

router = APIRouter()


@router.get("", response_model=DownloadRequestsResult)
async def get_downloads(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(kc_service.require_admin()),
):
    """Download requests, most recent first (admin)."""
    return await list_requests(session, skip, limit)


@router.post("/estimate", response_model=DownloadEstimate)
async def post_estimate(
    selection: DownloadSelection, session: AsyncSession = Depends(get_session)
):
    """Records and datasets a download of the selection would cover (upper
    bound), the studies left out by embargo, and the record limit."""
    return await estimate(session, selection)


@router.post("", response_model=DownloadAccepted, status_code=202)
async def post_download(
    form: DownloadForm,
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    engine: AsyncEngine = Depends(get_engine),
):
    """Queue a download; the link is emailed when the archive is ready.
    Behind a proxy, set FORWARDED_ALLOW_IPS to it for the client IP."""
    client_ip = request.client.host if request.client else None
    download = await create_request(session, form, client_ip)
    # start on this pod now; any pod's poll picks it up otherwise
    background_tasks.add_task(claim_and_run, engine)
    return DownloadAccepted(
        id=download.id, status=download.status, n_records=download.n_records
    )


@router.get("/{token}")
async def get_download(token: str, session: AsyncSession = Depends(get_session)):
    download = await find_by_token(session, token)
    if download is None:
        raise HTTPException(status_code=404, detail="unknown download link")
    expired = download.expires_at and download.expires_at < datetime.now(timezone.utc)
    if download.status != "ready" or expired:
        raise HTTPException(status_code=410, detail="this download link has expired")
    # headers are latin-1: an ASCII fallback, the unicode name in filename*
    name = safe_name(download.title)
    ascii_name = re.sub(r"[^\w.-]+", "_", name, flags=re.ASCII).strip("_") or "download"
    return StreamingResponse(
        stream_archive(download.s3_key),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{ascii_name}.zip";'
            f" filename*=UTF-8''{quote(name)}.zip",
            "Content-Length": str(download.size),
        },
    )
