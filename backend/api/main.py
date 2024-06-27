import os
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from logging import info, basicConfig, INFO
from pydantic import BaseModel
from api.db import init_client
from api.models import init_models
from api.views.seed import router as seed_router
from api.views.catalog import router as catalog_router
from api.views.map import router as map_router

basicConfig(level=INFO)

PATH_PREFIX = os.environ['PATH_PREFIX']


@asynccontextmanager
async def db_lifespan(app: FastAPI):
    # Startup
    app.client = init_client()
    app.database = app.client.get_default_database()
    ping_response = await app.database.command("ping")
    if int(ping_response["ok"]) != 1:
        raise Exception("Problem connecting to database.")
    else:
        info("Connected to database.")
    await init_models(app.client)

    yield

    # Shutdown
    info("Closing connection to database.")
    app.client.close()


app: FastAPI = FastAPI(root_path=PATH_PREFIX, lifespan=db_lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range"],
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
async def get_health() -> HealthCheck:
    """
    Endpoint to perform a healthcheck on for kubenernetes liveness and
    readiness probes.
    """
    # Check DB connection
    try:
        await app.database.command("ping")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Error: {e}")

    return HealthCheck(status="OK")

app.include_router(
    seed_router,
    prefix="/seed",
    tags=["Seed"],
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
