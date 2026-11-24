"""Rebuild api/data/benchmarks.csv from the science team's benchmark workbook
(see docs/202-reference-values.md).

    uv run python -m api.scripts.import_benchmarks path/to/workbook.xlsx

Workbook rows replace the rows with a sheet prefix (co2-, tvoc-, voc-,
radon-, pm-); the other rows (who-*) are kept by hand. Any text the tables
below do not know stops the script: a new wording needs a decision here.
The CSV changes only when the backend accepts the result."""

import argparse
import csv
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from api.models.measurement import Parameter
from api.services.parameter import BENCHMARKS_CSV, read_benchmarks, read_parameters
from openpyxl import load_workbook

# sheet -> id prefix
SHEETS = {
    "CO2": "co2",
    "TVOC": "tvoc",
    "Individual VOC": "voc",
    "Radon": "radon",
    "PM": "pm",
}
# lists for the workbook's own drop-downs, no reference in it
IGNORED_SHEETS = ("Drop-down list",)

COLUMNS = [
    "id",
    "parameter",
    "is_default",
    "source",
    "institution",
    "year",
    "region",
    "limit_type",
    "legal_status",
    "setting",
    "averaging",
    "period",
    "value",
    "unit",
    "qualifier",
    "url",
    "note",
]

# workbook pollutant names that are not a parameter label, or that are the
# label of more than one parameter
ALIASES = {
    "carbon dioxide (co2)": "co2",
    "total volatile organic compounds (tvoc)": "tvoc",
    "pm2.5": "pm2_5",
    "pm10": "pm10",
    "ufp (particle number)": "total_ufp",
    # other names of the same compound
    "2-butanone (mek)": "methyl_ethyl_ketone",
    "2-butanone (methyl ethyl ketone)": "methyl_ethyl_ketone",
    "4-methyl-2-pentanone": "methyl_isobutyl_ketone",
    "methyl isobutyl ketone (mibk)": "methyl_isobutyl_ketone",
    "2-furaldehyde": "furfural",
    "propan-1,2-diol": "propylene_glycol",
    "d-limonene": "limonene",
    "alpha-pinene": "alpha_pinene",
    "n-hexane": "hexane",
    "ethylene glycol monobutyl ether (egbe)": "2_butoxyethanol",
}

# assumed outdoor CO2 level for references given in ppm above outdoor
OUTDOOR_CO2_PPM = 400

# workbook unit -> unit to convert from, and what the note says
UNITS = {
    "ppm above outdoor": "ppm",
    "particles/cm³": "#/cm³",
    "µg/Nm³": "µg/m³",
}

# the averaging period in the workbook's words -> what Explore compares it
# with: hourly means, daily means or the long-term mean of each space;
# None skips the row
PERIODS: dict[str, str | None] = {
    # hourly means: one hour or less, or no stated period
    "1 h": "hour",
    "1 hour": "hour",
    "15 min": "hour",
    "30 min": "hour",
    "20–30 min (single measurement)": "hour",
    "1–4 h during occupancy": "hour",
    "More than 1 h": "hour",
    "Sustained period, e.g. approximately 1 h": "hour",
    "Not more than 20 consecutive minutes/day": "hour",
    "Post-construction testing (1 h closed-window preparation"
    " for natural ventilation)": "hour",
    "Acceptance-test sampling (not an 8-hour TWA)": "hour",
    "Momentary": "hour",
    "Single measurement": "hour",
    "At any time during measurement": "hour",
    "At maximum occupancy": "hour",
    "Consistent concentration": "hour",
    "Design conditions": "hour",
    "During use": "hour",
    "Normal use": "hour",
    "Average": "hour",
    "Average of measurements": "hour",
    "Arithmetic mean over measurement interval": "hour",
    "Average from beginning to end of lessons": "hour",
    "Short term": "hour",
    "Short-term ceiling": "hour",
    "Short-term; repeated throughout day": "hour",
    "Short-term or long-term sampling": "hour",
    "Not specified": "hour",
    "Not specified (rapid-action concentration)": "hour",
    "Not specified in online summary": "hour",
    "Not given (general)": "hour",
    "Sampling duration not specified in row": "hour",
    "Sample duration per measurement method": "hour",
    "Sampling time specified by measurement method": "hour",
    # daily means: 24 hours, or a working day
    "24 h": "day",
    "24 hours": "day",
    "Daily (24 h)": "day",
    "8 h": "day",
    "8 hours": "day",
    "8-hour average": "day",
    "8-hour TWA": "day",
    "95% of use time, maximum 8 h": "day",
    "Up to 10-hour TWA": "day",
    "Daily average during occupied period": "day",
    "Average during daily use period": "day",
    "Arithmetic mean over representative assessment period": "day",
    "Test method per national implementing rule": "day",
    # long-term mean of each space: a week or more
    "Annual": "long_term",
    "Annual average": "long_term",
    "1 year": "long_term",
    "1 year (as reported)": "long_term",
    ">1 year": "long_term",
    "14 days–1 year": "long_term",
    "1–14 days": "long_term",
    "4–7 days sample": "long_term",
    "4.5–7 days": "long_term",
    "7-day active sample": "long_term",
    "Minimum 1 week": "long_term",
    "Long term": "long_term",
    "Long-term (months to years)": "long_term",
    "Long-term exposure": "long_term",
    "Long-term / typical indoor conditions": "long_term",
    "Chronic (>365 days, lifetime context)": "long_term",
    "Indoor ²²²Rn activity concentration;"
    " converted from 2 pCi/L using 1 pCi/L = 37 Bq/m³": "long_term",
    "Indoor ²²²Rn activity concentration;"
    " converted from 4 pCi/L using 1 pCi/L = 37 Bq/m³": "long_term",
    # contaminated-land clean-up, not an indoor exposure
    "Remediation scenario (no fixed sample-average)": None,
}

# region spellings that name the same place
REGIONS = {
    "Worldwide (WHO)": "Worldwide",
    "UK": "United Kingdom",
    "England (UK)": "United Kingdom – England",
    "USA": "United States",
    "USA – New Jersey": "United States – New Jersey",
    "USA – New York City": "United States – New York City",
    "UAE": "United Arab Emirates",
    "UAE – Dubai": "United Arab Emirates – Dubai",
    "Czech Republic": "Czechia",
    "Hong Kong SAR": "Hong Kong",
    "Russian Federation": "Russia",
}

# the reference Explore shows first; other parameters take their first
# worldwide row, else their first row
DEFAULTS = {
    "co2": "co2-8",  # EN 16798-1:2019 Category II
    "pm2_5": "pm-2",  # WHO AQG 2021, 24 hours
    "pm10": "pm-4",  # WHO AQG 2021, 24 hours
    "radon": "radon-1",  # WHO 2009, annual
    "formaldehyde": "voc-252",  # WHO 2010, 30 min
    "naphthalene": "voc-253",  # WHO 2010, 1 year
    "total_ufp": "pm-310",  # WHO AQG 2021 good practice, 24 hours
}


@dataclass
class Skipped:
    reason: str
    name: str


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--out", type=Path, default=BENCHMARKS_CSV)
    args = parser.parse_args()
    parameters = {p.slug: p for p in read_parameters()}
    rows, skipped = read_workbook(args.workbook, parameters)
    kept = [r for r in read_rows(args.out) if not _from_workbook(r["id"])]
    rows = with_defaults(kept, rows)
    write_checked(args.out, kept + rows, parameters)
    print(f"{len(rows)} workbook rows and {len(kept)} kept rows in {args.out}")
    for (reason, name), count in sorted(
        Counter((s.reason, s.name) for s in skipped).items()
    ):
        print(f"skipped {count:3d} {reason}: {name}", file=sys.stderr)


def read_workbook(
    path: Path, parameters: dict[str, Parameter]
) -> tuple[list[dict], list[Skipped]]:
    by_label: dict[str, list[str]] = defaultdict(list)
    for p in parameters.values():
        by_label[p.label.casefold()].append(p.slug)
    rows: list[dict] = []
    skipped: list[Skipped] = []
    workbook = load_workbook(path, read_only=True, data_only=True)
    for sheet in workbook.worksheets:
        if sheet.title in IGNORED_SHEETS:
            continue
        if sheet.title not in SHEETS:
            raise ValueError(f"unknown sheet '{sheet.title}'")
        lines = sheet.iter_rows(values_only=True)
        header = [_text(h) for h in next(lines)]
        for cells in lines:
            cell = dict(zip(header, cells))
            if cell.get("Parameter") in (None, ""):
                continue
            where = f"{sheet.title} row n={cell.get('n')}"
            name = _text(cell["Parameter"])
            key = name.casefold()
            slugs = [ALIASES[key]] if key in ALIASES else by_label.get(key, [])
            if len(slugs) > 1:
                raise ValueError(
                    f"{where}: '{name}' is the label of {slugs}, add it to ALIASES"
                )
            if not slugs:
                skipped.append(Skipped("no such parameter", name))
                continue
            slug = slugs[0]
            period = _text(cell["Average period"])
            if period not in PERIODS:
                raise ValueError(
                    f"{where}: unknown period '{period}', add it to PERIODS"
                )
            averaging = PERIODS[period]
            if averaging is None:
                skipped.append(Skipped("not an indoor exposure", period))
                continue
            value, unit, note = _canonical(where, cell, parameters[slug])
            region = _text(cell["Country / Spatial extent"])
            rows.append(
                {
                    "id": f"{SHEETS[sheet.title]}-{_number(where, cell['n'])}",
                    "parameter": slug,
                    "is_default": "false",
                    "source": _text(cell["Reference"]),
                    "institution": _text(cell["Institution"]),
                    "year": _year(where, cell["Year"]),
                    "region": REGIONS.get(region, region),
                    "limit_type": _text(cell["Type of limit"]),
                    "legal_status": _text(cell["Legal status"]),
                    "setting": _text(cell["Building type"]),
                    "averaging": averaging,
                    "period": period,
                    "value": _format(value),
                    "unit": unit,
                    "qualifier": _text(cell["Value Qualifier"]),
                    "url": _text(cell["URL"]),
                    "note": note,
                }
            )
    return rows, skipped


def _canonical(where: str, cell: dict, parameter: Parameter) -> tuple[float, str, str]:
    """The value in the parameter's canonical unit, and a note on what changed."""
    given = cell["Value"]
    if not isinstance(given, (int, float)):
        raise ValueError(f"{where}: value '{given}' is not a number")
    unit = _text(cell["Unit"])
    source_unit = UNITS.get(unit, unit)
    value = float(given)
    notes = []
    if unit == "ppm above outdoor":
        value += OUTDOOR_CO2_PPM
        notes.append(
            f"{_format(given)} ppm above outdoor, plus an assumed outdoor level"
            f" of {OUTDOOR_CO2_PPM} ppm"
        )
    elif unit == "µg/Nm³":
        notes.append("Given in µg/Nm³ (normal conditions), read as µg/m³")
    conversions = parameter.conversions
    if (
        source_unit == "mg/m³"
        and source_unit not in conversions
        and "µg/m³" in conversions
    ):
        value, source_unit = value * 1000, "µg/m³"
    conversion = conversions.get(source_unit)
    if conversion is None:
        raise ValueError(f"{where}: no conversion from '{unit}' to '{parameter.unit}'")
    value = value * conversion["factor"] + conversion.get("offset", 0.0)
    if source_unit != parameter.unit or unit == "mg/m³":
        notes.append(f"Converted from {_format(given)} {unit}")
    return value, parameter.unit, "; ".join(notes)


def with_defaults(kept: list[dict], rows: list[dict]) -> list[dict]:
    """Mark one workbook row per parameter as default, unless a kept row is."""
    kept_defaults = {r["parameter"] for r in kept if r["is_default"] == "true"}
    ids = {r["id"]: r for r in rows}
    for slug, identifier in DEFAULTS.items():
        if slug in kept_defaults:
            raise ValueError(
                f"'{slug}' has a default among the kept rows and in DEFAULTS"
            )
        if ids.get(identifier, {}).get("parameter") != slug:
            raise ValueError(f"DEFAULTS: '{identifier}' is not a row of '{slug}'")
        ids[identifier]["is_default"] = "true"
    for slug in dict.fromkeys(r["parameter"] for r in rows):
        if slug in kept_defaults or slug in DEFAULTS:
            continue
        own = [r for r in rows if r["parameter"] == slug]
        first = next((r for r in own if r["region"] == "Worldwide"), own[0])
        first["is_default"] = "true"
    return rows


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_checked(path: Path, rows: list[dict], parameters: dict[str, Parameter]):
    """Replace path with rows only if the backend accepts them: a refused
    result leaves the current CSV as it is."""
    draft = path.with_name(f"{path.name}.new")
    try:
        write_rows(draft, rows)
        read_benchmarks(draft, parameters)
        draft.replace(path)
    finally:
        draft.unlink(missing_ok=True)


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _from_workbook(identifier: str) -> bool:
    return identifier.split("-", 1)[0] in SHEETS.values()


def _text(value) -> str:
    """A cell as one line of text, blank for an empty cell."""
    return " ".join(str(value).split()) if value is not None else ""


def _number(where: str, value) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{where}: row number '{value}' is not an integer")
    return value


def _year(where: str, value) -> str:
    if value is None or _text(value) in ("", "Not specified"):
        return ""
    if not isinstance(value, int):
        raise ValueError(f"{where}: year '{value}' is not an integer")
    return str(value)


def _format(value: float) -> str:
    return f"{value:.6g}"


if __name__ == "__main__":
    main()
