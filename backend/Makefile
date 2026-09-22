env_path=../.env

install:
	uv sync

run:
	uv run dotenv -f "$(env_path)" run uvicorn api.main:app

lint:
	uv run pre-commit run --all-files

db-upgrade:
	uv run dotenv -f "$(env_path)" run alembic upgrade head

db-downgrade:
	uv run dotenv -f "$(env_path)" run alembic downgrade -1

db-revision:
	uv run dotenv -f "$(env_path)" run alembic revision --autogenerate -m "$(name)"

# `make seed` imports all of SEED_DATA, `make seed <identifier>...` only those studies
seed_studies := $(filter-out seed seed-check,$(MAKECMDGOALS))

seed:
	uv run dotenv -f "$(env_path)" run python -m api.scripts.seed $(seed_studies)

seed-check:
	uv run dotenv -f "$(env_path)" run python -m api.scripts.seed --check $(seed_studies)

ifneq ($(filter seed seed-check,$(MAKECMDGOALS)),)
$(seed_studies):
	@:
endif
