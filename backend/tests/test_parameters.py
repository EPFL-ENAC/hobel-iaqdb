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
    defaults = {b.parameter: b for b in benchmarks if b.is_default}
    assert set(defaults) == {b.parameter for b in benchmarks}
    # the defaults the plan names (docs/202-reference-values.md)
    assert (defaults["co2"].id, defaults["co2"].value) == ("co2-8", 1200)
    assert defaults["pm2_5"].id == "pm-2" and defaults["radon"].id == "radon-1"


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


BENCHMARK_HEADER = (
    "id,parameter,is_default,source,institution,year,region,limit_type,"
    "legal_status,setting,averaging,period,value,unit,qualifier,url,note\n"
)


def _benchmark(id: str, is_default: str = "true", averaging: str = "hour") -> str:
    return (
        f"{id},co2,{is_default},EN 16798-1,CEN,2019,Europe,Standard,,,"
        f"{averaging},1 h,1200,ppm,,,\n"
    )


def test_malformed_benchmarks_fail(tmp_path: Path):
    bad = tmp_path / "benchmarks.csv"
    cases = [
        (_benchmark("a", averaging="week"), "averaging not in"),
        (_benchmark("a") + _benchmark("a", "false"), "duplicate id 'a'"),
        (_benchmark("a") + _benchmark("b"), "'co2' has 2 defaults, expected 1"),
        (_benchmark("a", "false"), "'co2' has 0 defaults, expected 1"),
        (_benchmark("a", "yes"), "is_default must be true or false"),
        (_benchmark("a").replace(",ppm,", ",ppb,"), "unit must be 'ppm'"),
    ]
    for rows, error in cases:
        bad.write_text(BENCHMARK_HEADER + rows)
        with pytest.raises(ValueError, match=error):
            read_benchmarks(bad)
    bad.write_text(BENCHMARK_HEADER + _benchmark("a") + _benchmark("b", "false"))
    assert [b.id for b in read_benchmarks(bad)] == ["a", "b"]


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
