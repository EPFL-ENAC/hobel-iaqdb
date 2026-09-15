FROM python:3.11.7-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /uvx /bin/
ENV PYTHONPATH="$PYTHONPATH:/app" \
  UV_PROJECT_ENVIRONMENT=/usr/local \
  UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update && apt-get install -y g++ libpq-dev libgl1 gdal-bin libgdal-dev && \
  rm -rf /var/lib/apt/lists/*

COPY uv.lock pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-dev

COPY alembic.ini start.sh /app/
COPY migrations /app/migrations
COPY api /app/api

ENTRYPOINT sh start.sh
