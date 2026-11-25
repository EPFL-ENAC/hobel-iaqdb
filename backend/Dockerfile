# Ubuntu: Debian images carry unfixed HIGH CVEs that fail the Trivy scan, and
# Alpine has no musl wheels for duckdb and rasterio. Python is the distribution's
# so that it is patched with it and visible to the scan.
FROM ubuntu:24.04 AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /bin/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
  UV_PYTHON=/usr/bin/python3 \
  UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy

# git: enacit4r-* dependencies; gcc, libpq-dev and python3-dev: psycopg2 has no wheel
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates gcc git libc6-dev libpq-dev python3-dev && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY uv.lock pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-dev

FROM ubuntu:24.04
ENV PYTHONPATH=/app \
  PATH="/opt/venv/bin:$PATH"

# libexpat1: needed by the rasterio wheel
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
  ca-certificates libexpat1 libpq5 python3 tzdata && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY alembic.ini start.sh /app/
COPY migrations /app/migrations
COPY api /app/api

ENTRYPOINT ["sh", "start.sh"]
