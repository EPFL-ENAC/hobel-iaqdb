"""The benchmark table: the rules a reference must meet, and its replacement
by the import script (docs/202-reference-values.md)."""

import pytest
from api.services.benchmark import BenchmarkService, parse_benchmarks
from api.services.catalog_version import CatalogVersionService
from api.services.parameter import read_parameters


def benchmark_row(
    id: str,
    is_default: str = "true",
    parameter: str = "co2",
    unit: str = "ppm",
    value: str = "1200",
    averaging: str = "hour",
    region: str = "Europe",
) -> dict:
    return {
        "id": id,
        "parameter": parameter,
        "is_default": is_default,
        "source": "EN 16798-1",
        "institution": "CEN",
        "year": "2019",
        "region": region,
        "limit_type": "Standard",
        "averaging": averaging,
        "period": "1 h",
        "value": value,
        "unit": unit,
        "url": "https://example.org",
    }


@pytest.fixture
def parameters():
    return {p.slug: p for p in read_parameters()}


def test_malformed_benchmarks_fail(parameters):
    cases = [
        ([benchmark_row("a", averaging="week")], "averaging not in"),
        ([benchmark_row("a"), benchmark_row("a", "false")], "duplicate id 'a'"),
        (
            [benchmark_row("a"), benchmark_row("b")],
            "'co2' has 2 defaults, expected 1",
        ),
        ([benchmark_row("a", "false")], "'co2' has 0 defaults, expected 1"),
        ([benchmark_row("a", "yes")], "is_default must be true or false"),
        ([benchmark_row("a", unit="ppb")], "a: unit must be 'ppm'"),
        ([benchmark_row("a", parameter="nope")], "unknown parameter 'nope'"),
        ([{**benchmark_row("a"), "source": ""}], r"a: missing \['source'\]"),
    ]
    for rows, error in cases:
        with pytest.raises(ValueError, match=error):
            parse_benchmarks(rows, parameters)
    rows = [benchmark_row("a"), benchmark_row("b", "false")]
    assert [b.id for b in parse_benchmarks(rows, parameters)] == ["a", "b"]


async def test_replace_writes_only_a_change(session, parameters):
    service = BenchmarkService(session)
    rows = [benchmark_row("a"), benchmark_row("b", "false")]
    assert await service.replace(parse_benchmarks(rows, parameters))
    await session.commit()
    assert [b.id for b in await service.all()] == ["a", "b"]
    assert await CatalogVersionService(session).get() == 2
    # the same references again: nothing to invalidate
    assert not await service.replace(parse_benchmarks(rows, parameters))
    await session.commit()
    assert await CatalogVersionService(session).get() == 2
    # a changed value and a removed row
    rows = [benchmark_row("a", value="1000")]
    assert await service.replace(parse_benchmarks(rows, parameters))
    await session.commit()
    assert [(b.id, b.value) for b in await service.all()] == [("a", 1000)]
    assert await CatalogVersionService(session).get() == 3
