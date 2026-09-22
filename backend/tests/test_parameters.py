from pathlib import Path

import pytest
from api.models.measurement import Parameter
from api.services.parameter import ParameterService, read_benchmarks, read_parameters
from sqlmodel import select


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
    bad.write_text("slug,label,reference,unit,conversions\nco2,CO2,carbon dioxide,,{}\n")
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
