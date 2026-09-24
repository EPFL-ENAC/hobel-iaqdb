from pathlib import Path

import pytest
from api.models.measurement import Benchmark, Parameter
from api.services.catalog_version import CatalogVersionService
from api.services.parameter import ParameterService, read_benchmarks, read_parameters
from sqlmodel import delete, select, update


def test_dictionary_is_well_formed():
    parameters = read_parameters()
    slugs = [p.slug for p in parameters]
    assert len(slugs) == len(set(slugs))
    assert {"co2", "pm2_5", "air_temperature"} <= set(slugs)
    benchmarks = read_benchmarks()
    assert {b.parameter for b in benchmarks} <= set(slugs)


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
    assert len(await service.benchmarks()) == len(read_benchmarks())
    # the dictionary already matched the CSVs: nothing to invalidate
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
    # a changed benchmark is a change too
    await session.exec(delete(Benchmark))
    await session.commit()
    await service.sync()
    await session.commit()
    assert await CatalogVersionService(session).get() == 3
