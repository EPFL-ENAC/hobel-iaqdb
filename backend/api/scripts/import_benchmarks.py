"""Replace the reference values of one database with a benchmarks CSV
(see docs/202-reference-values.md).

    make import-benchmarks

The make target reads data/benchmarks.csv at the repository root, and
`csv=path/to/benchmarks.csv` reads another file. The CSV has the columns of
COLUMNS in api/services/benchmark.py, with each value in the canonical unit
of its parameter. The database is the one DB_HOST, DB_PORT and DB_NAME
name, so a port-forward reaches dev or prod. The CSV replaces the whole
benchmark table in one transaction: a refused CSV keeps the current
references."""

import argparse
import asyncio
from pathlib import Path

from api.config import config
from api.services.benchmark import BenchmarkService, parse_benchmarks, read_csv
from api.services.parameter import ParameterService
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv", type=Path)
    parser.add_argument(
        "--check", action="store_true", help="validate only, write nothing"
    )
    parser.add_argument(
        "--allow-prod",
        action="store_true",
        help="write even when S3_PATH_PREFIX points at production",
    )
    args = parser.parse_args()
    asyncio.run(run(args.csv, args.check, args.allow_prod))


async def run(path: Path, check_only: bool = False, allow_prod: bool = False):
    """Check the CSV against the parameters of the target database, then
    replace its references (or only report, with `check_only`)."""
    if not check_only and not allow_prod and "prod" in config.S3_PATH_PREFIX:
        raise RuntimeError(
            f"Refusing to write into S3_PATH_PREFIX={config.S3_PATH_PREFIX}"
            " (pass --allow-prod to write to production on purpose)"
        )
    rows = read_csv(path)
    target = f"{config.DB_NAME} on {config.DB_HOST}:{config.DB_PORT}"
    engine = create_async_engine(config.DB_URL)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            parameters = {p.slug: p for p in await ParameterService(session).all()}
            if not parameters:
                raise RuntimeError(
                    f"{target} has no parameter: start its backend once, so it"
                    " fills the dictionary"
                )
            benchmarks = parse_benchmarks(rows, parameters)
            if check_only:
                print(
                    f"{len(benchmarks)} references valid for {target}, nothing written"
                )
                return
            changed = await BenchmarkService(session).replace(benchmarks)
            await session.commit()
    finally:
        await engine.dispose()
    if changed:
        print(f"{len(benchmarks)} references written to {target}")
    else:
        print(f"{target} already holds these {len(benchmarks)} references")


if __name__ == "__main__":
    main()
