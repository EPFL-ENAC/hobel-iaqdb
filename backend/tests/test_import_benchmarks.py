"""The benchmark workbook import (docs/202-reference-values.md), on a small
workbook built here with the science team's column names."""

from pathlib import Path

import pytest
from api.scripts import import_benchmarks
from api.scripts.import_benchmarks import read_workbook, with_defaults, write_rows
from api.services.parameter import read_parameters
from openpyxl import Workbook

HEADER = [
    "n ",
    "Parameter",
    "Value",
    "Unit",
    "Average period",
    "Value Qualifier",
    "Reference",
    "Institution",
    "Year",
    "Country / Spatial extent",
    "Type of limit",
    "Legal status",
    "Building type",
    "URL",
]


def _row(n, parameter, value, unit, period="1 h", region="Worldwide", year=2021):
    return [
        n,
        parameter,
        value,
        unit,
        period,
        "Maximum",
        f"Reference {n}",
        "Institution",
        year,
        region,
        "Guideline",
        "Binding",
        "Offices",
        "https://example.org",
    ]


def _workbook(path: Path, sheets: dict[str, list[list]]) -> Path:
    workbook = Workbook()
    workbook.remove(workbook.active)
    for title, rows in sheets.items():
        sheet = workbook.create_sheet(title)
        sheet.append(HEADER)
        for row in rows:
            sheet.append(row)
    workbook.save(path)
    return path


@pytest.fixture
def parameters():
    return {p.slug: p for p in read_parameters()}


def test_rows_are_converted_to_the_canonical_unit(tmp_path, parameters):
    path = _workbook(
        tmp_path / "bench.xlsx",
        {
            "CO2": [_row(1, "Carbon dioxide (CO2)", 800, "ppm above outdoor")],
            "TVOC": [_row(1, "Total volatile organic compounds (TVOC)", 400, "µg/m³")],
            "Individual VOC": [
                _row(1, "Formaldehyde", 0.1, "mg/m³", period="30 min"),
                _row(2, "Benzene", 0.005, "mg/m³", period="Annual", region="UK"),
                _row(3, "2-Butanone (MEK)", 5000, "µg/m³", period="24 h"),
                _row(4, "Styrene", 260, "µg/m³"),
                _row(
                    5,
                    "Benzene",
                    5,
                    "µg/m³",
                    period="Remediation scenario (no fixed sample-average)",
                ),
            ],
        },
    )
    rows, skipped = read_workbook(path, parameters)
    by_id = {r["id"]: r for r in rows}
    co2 = by_id["co2-1"]
    assert (co2["parameter"], co2["value"], co2["unit"]) == ("co2", "1200", "ppm")
    assert "assumed outdoor level of 400 ppm" in co2["note"]
    assert co2["averaging"] == "hour" and co2["year"] == "2021"
    tvoc = by_id["tvoc-1"]
    assert (tvoc["value"], tvoc["unit"]) == ("97.8", "ppb")
    assert tvoc["note"] == "Converted from 400 µg/m³"
    assert by_id["voc-1"]["value"] == "100"
    # benzene has no mg/m³ factor: mg/m³ goes through µg/m³
    benzene = by_id["voc-2"]
    assert (benzene["value"], benzene["averaging"]) == ("5", "long_term")
    assert benzene["region"] == "United Kingdom"
    assert by_id["voc-3"]["parameter"] == "methyl_ethyl_ketone"
    assert by_id["voc-3"]["averaging"] == "day"
    assert {(s.reason, s.name) for s in skipped} == {
        ("no such parameter", "Styrene"),
        (
            "not an indoor exposure",
            "Remediation scenario (no fixed sample-average)",
        ),
    }


def test_unknown_text_stops_the_import(tmp_path, parameters):
    path = _workbook(
        tmp_path / "period.xlsx",
        {"CO2": [_row(1, "Carbon dioxide (CO2)", 1000, "ppm", period="2 weeks")]},
    )
    with pytest.raises(ValueError, match="unknown period '2 weeks'"):
        read_workbook(path, parameters)
    path = _workbook(
        tmp_path / "unit.xlsx",
        {"CO2": [_row(1, "Carbon dioxide (CO2)", 1000, "mg/m³")]},
    )
    with pytest.raises(ValueError, match="no conversion from 'mg/m³'"):
        read_workbook(path, parameters)
    path = _workbook(tmp_path / "sheet.xlsx", {"NO2": []})
    with pytest.raises(ValueError, match="unknown sheet 'NO2'"):
        read_workbook(path, parameters)
    # particle_number_concentration and particle_number share this label
    path = _workbook(
        tmp_path / "label.xlsx",
        {"PM": [_row(1, "Particle number concentration", 1000, "#/cm³")]},
    )
    with pytest.raises(ValueError, match="add it to ALIASES"):
        read_workbook(path, parameters)


def test_a_refused_result_keeps_the_csv(tmp_path, monkeypatch):
    out = tmp_path / "benchmarks.csv"
    kept = {
        "id": "who-benzene",
        "parameter": "benzene",
        "is_default": "false",
        "source": "Source",
        "institution": "WHO",
        "region": "Worldwide",
        "limit_type": "Guideline",
        "averaging": "day",
        "period": "24 hours",
        "value": "5",
        "unit": "µg/m³",
    }
    write_rows(out, [kept])
    monkeypatch.setattr(import_benchmarks, "DEFAULTS", {})

    def run(*rows):
        path = _workbook(tmp_path / "bench.xlsx", {"Individual VOC": list(rows)})
        monkeypatch.setattr("sys.argv", ["import", str(path), "--out", str(out)])
        import_benchmarks.main()

    run(_row(1, "Benzene", 2, "µg/m³"))
    accepted = out.read_text(encoding="utf-8")
    assert "voc-1,benzene,true" in accepted
    # without a benzene row, the kept who-benzene row has no default
    with pytest.raises(ValueError, match="'benzene' has 0 defaults"):
        run(_row(2, "Toluene", 200, "µg/m³"))
    assert out.read_text(encoding="utf-8") == accepted
    assert not (tmp_path / "benchmarks.csv.new").exists()


def test_defaults(monkeypatch):
    rows = [
        {"id": "voc-1", "parameter": "benzene", "region": "France"},
        {"id": "voc-2", "parameter": "benzene", "region": "Worldwide"},
        {"id": "voc-3", "parameter": "toluene", "region": "France"},
        {"id": "co2-1", "parameter": "co2", "region": "Europe"},
        {"id": "co2-2", "parameter": "co2", "region": "Worldwide"},
    ]
    for row in rows:
        row["is_default"] = "false"
    monkeypatch.setattr(import_benchmarks, "DEFAULTS", {"co2": "co2-1"})
    marked = with_defaults([], rows)
    defaults = {r["parameter"]: r["id"] for r in marked if r["is_default"] == "true"}
    # an explicit choice, else the first worldwide row, else the first row
    assert defaults == {"co2": "co2-1", "benzene": "voc-2", "toluene": "voc-3"}
    monkeypatch.setattr(import_benchmarks, "DEFAULTS", {"co2": "voc-1"})
    with pytest.raises(ValueError, match="'voc-1' is not a row of 'co2'"):
        with_defaults([], rows)
    monkeypatch.setattr(import_benchmarks, "DEFAULTS", {"co2": "co2-1"})
    kept = [{"id": "who-co2", "parameter": "co2", "is_default": "true"}]
    with pytest.raises(ValueError, match="'co2' has a default among the kept rows"):
        with_defaults(kept, rows)
