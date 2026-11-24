from pathlib import Path

import pytest
from api.models.measurement import Parameter
from api.services.benchmark import BenchmarkService, parse_benchmarks
from api.services.catalog_version import CatalogVersionService
from api.services.parameter import ParameterService, read_parameters
from sqlmodel import select, update
from tests.test_benchmarks import benchmark_row


def test_dictionary_is_well_formed():
    parameters = read_parameters()
    slugs = [p.slug for p in parameters]
    assert len(slugs) == len(set(slugs))
    assert {"co2", "pm2_5", "air_temperature"} <= set(slugs)


def test_malformed_dictionary_fails(tmp_path: Path):
    bad = tmp_path / "parameters.csv"
    bad.write_text(
        "slug,label,reference,unit,conversions\n"
        'co2,CO2,carbon dioxide,ppm,"{""ppb"": {""factor"": 0.001}}"\n'
    )
    with pytest.raises(ValueError, match="canonical unit"):
        read_parameters(bad)
    bad.write_text(
        "slug,label,reference,unit,conversions\nco2,CO2,carbon dioxide,,{}\n"
    )
    with pytest.raises(ValueError, match="missing"):
        read_parameters(bad)


async def test_sync_is_idempotent(session):
    service = ParameterService(session)
    n = await service.sync()
    await session.commit()
    again = await service.sync()
    await session.commit()
    assert n == again
    rows = (await session.exec(select(Parameter))).all()
    assert len(rows) == n
    # the dictionary already matched the CSV: nothing to invalidate
    assert await CatalogVersionService(session).get() == 1


async def test_sync_bumps_version_when_dictionary_changed(session):
    service = ParameterService(session)
    await session.exec(
        update(Parameter).where(Parameter.slug == "co2").values(label="stale")
    )
    await session.commit()
    await service.sync()
    await session.commit()
    co2 = await session.get(Parameter, "co2")
    await session.refresh(co2)
    assert co2.label != "stale"
    assert await CatalogVersionService(session).get() == 2


async def test_sync_keeps_the_imported_benchmarks(session):
    """The references come from the import script only: the boot sync of a
    new release must not drop the ones a database already holds."""
    parameters = {p.slug: p for p in read_parameters()}
    await BenchmarkService(session).replace(
        parse_benchmarks([benchmark_row("a")], parameters)
    )
    await session.commit()
    await ParameterService(session).sync()
    await session.commit()
    assert [b.id for b in await BenchmarkService(session).all()] == ["a"]
