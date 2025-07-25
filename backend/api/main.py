from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.config import config
from api.db import get_session, AsyncSession
from logging import basicConfig, INFO
from pydantic import BaseModel
from sqlalchemy.sql import text
from api.views.catalog import router as catalog_router
from api.views.stats import router as stats_router
from api.views.contribute import router as contribute_router
from api.views.map import router as map_router
from api.views.files import router as files_router

basicConfig(level=INFO)

app = FastAPI(root_path=config.PATH_PREFIX)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""
    status: str = "OK"


@app.get(
    "/healthz",
    tags=["Healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def get_health(
    session: AsyncSession = Depends(get_session),
) -> HealthCheck:
    """
    Endpoint to perform a healthcheck on for kubenernetes liveness and
    readiness probes.
    """
    # Check DB connection
    try:
        await session.exec(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Error: {e}")

    return HealthCheck(status="OK")

app.include_router(
    stats_router,
    prefix="/stats",
    tags=["Statistics"],
)

app.include_router(
    contribute_router,
    prefix="/contribute",
    tags=["Contribute"],
)

app.include_router(
    catalog_router,
    prefix="/catalog",
    tags=["Catalog"],
)

app.include_router(
    map_router,
    prefix="/map",
    tags=["Map"],
)

app.include_router(
    files_router,
    prefix="/files",
    tags=["Files"],
)
