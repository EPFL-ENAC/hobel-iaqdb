# FastAPI
Based loosely on https://github.com/gauravgola96/FastAPI-Example

## Requirements
- python 3.11 (see `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- Make
- Docker with docker compose
- OS:
  - Windows: docker desktop with wsl
  - Apple: with docker desktop dependencies installed via brew
  - Linux: libwebp-dev

## How to run
API for uploading object(.png|.jpg) to S3 bucket asynchronously
-> convert png or jpg to webp files

Create a file .env and put all s3 credential here
```
.env
```
s3 credentials

```
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
S3_REGION =
S3_BUCKET =
S3_PATH_PREFIX =

```


Run Locally
```
make install; make run
```

## Database

The API needs a TimescaleDB instance (Postgres 15 with the `timescaledb`
extension preloaded). The compose file provides one:

```
docker compose up -d postgres   # from the repository root
make db-upgrade                 # apply the Alembic migrations
make run
```

`make run` does not run migrations (the container image does, via
`start.sh`), so run `make db-upgrade` after pulling a branch that adds one.
A startup error such as `relation "parameter" does not exist` means the
schema is behind. If the `postgres` volume was initialised by a plain
Postgres image, `CREATE EXTENSION timescaledb` fails with "must be
preloaded": either recreate the volume or run
`ALTER SYSTEM SET shared_preload_libraries = 'timescaledb'` and restart
the container.

Seeding loads the study metadata and the measurements from `SEED_DATA`
into the hypertable (`make seed`, or `make seed <identifier>...` for a
subset; `make seed-check` reports without writing). Design and load
budgets are in `docs/129-explore-charts-api.md`.

## Tests

Tests run against a throwaway TimescaleDB on port 5433 and refuse any
other port, so they never touch the development database:

```
make test-db   # start (or reset) the container
make test      # or: make test args="-k metadata"
make lint      # pre-commit: black, flake8, isort
```

Swagger docs
```
http://localhost:8000/docs
```

To provide .env use Dockerfile.
```
Path : ./Dockerfile
```

## Install
Don't forget to install libwebp-dev on the machine (cf Dockerfile)
