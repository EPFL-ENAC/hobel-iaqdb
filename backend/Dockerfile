FROM python:3.11.7-bullseye
ENV POETRY_VERSION=1.7.1
RUN pip install "poetry==$POETRY_VERSION"
ENV PYTHONPATH="$PYTHONPATH:/app"

WORKDIR /app

COPY poetry.lock pyproject.toml /app/
RUN poetry config installer.max-workers 10
RUN poetry config virtualenvs.create false
RUN apt-get update && apt-get install -y g++ libpq-dev libgl1
RUN poetry install --no-interaction

COPY alembic.ini start.sh /app/
COPY migrations /app/migrations
COPY api /app/api

ENTRYPOINT sh start.sh