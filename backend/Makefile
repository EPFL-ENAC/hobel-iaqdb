env_path=../.env

install:
	uv sync

run:
	uv run dotenv -f "$(env_path)" run uvicorn api.main:app

lint:
	uv run pre-commit run --all-files

# Tests run against a throwaway TimescaleDB on port 5433 (`make test-db`)
test_db_port := 5433
test_db_name := iaqdb-timescale-test

test-db:
	docker rm -f $(test_db_name) >/dev/null 2>&1 || true
	docker run -d --name $(test_db_name) -p $(test_db_port):5432 \
		-e POSTGRES_USER=$$(grep '^DB_USER=' $(env_path) | cut -d= -f2-) \
		-e POSTGRES_PASSWORD=$$(grep '^DB_PASSWORD=' $(env_path) | cut -d= -f2-) \
		-e POSTGRES_DB=$$(grep '^DB_NAME=' $(env_path) | cut -d= -f2-) \
		timescale/timescaledb:latest-pg18

test:
	DB_PORT=$(test_db_port) uv run dotenv -f "$(env_path)" run --no-override pytest $(args)

db-upgrade:
	uv run dotenv -f "$(env_path)" run alembic upgrade head

db-downgrade:
	uv run dotenv -f "$(env_path)" run alembic downgrade -1

db-revision:
	uv run dotenv -f "$(env_path)" run alembic revision --autogenerate -m "$(name)"

# `make data-upload` uploads all of UPLOAD_DATA, `make data-upload <identifier>...` only those studies
upload_studies := $(filter-out data-upload data-upload-check,$(MAKECMDGOALS))

data-upload:
	uv run dotenv -f "$(env_path)" run python -m api.scripts.data_upload $(upload_studies)

data-upload-check:
	uv run dotenv -f "$(env_path)" run python -m api.scripts.data_upload --check $(upload_studies)

ifneq ($(filter data-upload data-upload-check,$(MAKECMDGOALS)),)
$(upload_studies):
	@:
endif
