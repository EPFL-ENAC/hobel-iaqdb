---
status: accepted
issue: 202
last_updated: 2026-11-24
summary: Replace the CO2 placeholder with the science team's benchmark workbook, let Explore users pick a reference per pollutant, and show its source.
---

# 202: Reference values from the benchmark workbook

This plan covers #202, #214 and the first task of #232 ("Choose and describe
the reference level"). It extends the benchmark part of
[129-explore-charts-api.md](129-explore-charts-api.md).

## Problem

Explore compares each pollutant with one reference value. For CO2 this value
was a placeholder (800 ppm), drawn in red with a "placeholder" badge. The
science team now gives a workbook of references,
`260922_IAQDB_Benchmark_regulations.xlsx`. It has one sheet per pollutant
family: CO2, TVOC, Individual VOC, Radon and PM. Each row gives a value, a
unit and an averaging period. It also names the institution, the country,
the type of limit, the legal status, the building type and a URL.

The workbook holds 1,309 rows. 867 rows name a pollutant that the database
knows, and 442 rows name 194 other compounds. Many of the known rows use
averaging periods that Explore cannot compute today: all radon rows and
half of the PM rows are annual means.

## Decisions

1. The references live in the `benchmark` table only. The repository and
   the backend image hold no copy of them, and the backend only reads the
   table. You keep the references in `data/benchmarks.csv` at the
   repository root, a folder that git ignores. The CSV has one row per
   reference. Its first columns are `id`, `parameter`, `is_default`,
   `source`, `institution`, `year`, `region` and `limit_type`. The other
   columns are `legal_status`, `setting`, `averaging`, `period`, `value`,
   `unit`, `qualifier`, `url` and `note`. The script
   `api/scripts/import_benchmarks.py` loads the CSV into one database and
   replaces its references. A change to the references therefore needs no
   release: you load the CSV into dev or prod through a port-forward (see
   "Run the import").
2. A pollutant can have many references. Each reference has a stable id,
   `<sheet prefix>-<row n>` (for example `co2-8`, `pm-2`). Rows that are
   not in the workbook (WHO AQG 2021 for NO2, SO2, O3 and CO) have a
   hand-written id that starts with `who-`.
3. Exactly one reference per pollutant has `is_default` set. The import
   refuses a CSV that breaks this rule.
4. Explore shows a reference menu in each figure that draws a reference.
   Each figure keeps its own choice per pollutant, so a pick changes that
   figure only.
5. Each figure names the reference in one line under the chart, with a
   link to the URL. A tooltip gives the institution, year, region, type of
   limit and averaging period. The menu says that local rules can differ.
6. A new query grain, `space`, compares long-term references. It is the
   mean of each (dataset, space) over the selected period, computed from
   `measurement_day`. Most records are shorter than one year, and the
   figures say so.
7. The placeholder code path (`PLACEHOLDER_BENCHMARKS`, the
   `placeholder` flag) is deleted.

## Import rules

The import checks every row with the backend's rules
(`api/services/benchmark.py`), against the parameters of the target
database. Each row needs a known parameter and the canonical unit of that
parameter. It also needs a unique id and an averaging value of `hour`,
`day` or `long_term`. You must start the target backend once before the
import, so that its boot sync fills the dictionary. The script then replaces the whole table in one
transaction and bumps the catalog version, so no cached schema keeps the
old references. A refused CSV keeps the current references. If the table
already holds the same references, the script writes nothing. If a release
changes the canonical unit of a parameter, convert the values in the CSV
and load it into each database again.

## How the CSV was made from the workbook

A script converted the workbook into the first CSV once. The script is not
in the repository. If the science team changes the workbook, you edit the
CSV by hand with the rules below.

The conversion skipped a row in two cases:

- The pollutant is not in `parameters.csv` (for example styrene, acrolein).
  This skipped 442 rows.
- The period is a remediation scenario for contaminated land. This skipped
  14 rows.

The `region` column gives one name to each country, for example "United
Kingdom" for "UK".

Values are in the parameter's canonical unit, converted with the factors of
`parameters.csv`. The `note` column records the original value.

- `ppm above outdoor` (CO2): the conversion added a fixed outdoor level of
  400 ppm. Example: EN 16798-1 Category II, 800 ppm above outdoor, became
  1,200 ppm.
- `mg/m³` for a VOC without an `mg/m³` factor: the conversion multiplied
  by 1,000 to get µg/m³ first.
- TVOC in µg/m³ became ppb with the factor of `parameters.csv` (0.2445).
- `particles/cm³` is `#/cm³`. `µg/Nm³` is read as µg/m³.

### Averaging periods

The workbook period text maps to one of three averaging values. The
`period` column keeps the text of the workbook.

| Averaging | Query grain | Workbook periods (examples) |
| --- | --- | --- |
| `hour` | `hour` | 1 h, 30 min, 15 min, momentary, single measurement, "Not specified" |
| `day` | `day` | 24 h, daily, 8 h, 8-hour TWA, daily average during occupied period |
| `long_term` | `space` | annual, 1 year, long term, chronic, multi-day samples (4 to 14 days) |

Two choices need a check by the science team:

- "Not specified" (45 CO2 rows) is compared with hourly means.
- "8 h" and 8-hour TWAs are compared with daily means. This also moves the
  WHO O3 8-hour guideline from hourly to daily means.

### Defaults

| Pollutant | Default reference |
| --- | --- |
| CO2 | EN 16798-1:2019 Category II, 800 ppm above outdoor (1,200 ppm), hourly |
| PM2.5 | WHO AQG 2021, 15 µg/m³, 24-hour |
| PM10 | WHO AQG 2021, 45 µg/m³, 24-hour |
| Radon | WHO 2009, 100 Bq/m³, annual |
| Formaldehyde | WHO 2010, 100 µg/m³, 30 min |
| Ultrafine particles | WHO AQG 2021 good practice, 10,000 #/cm³, 24-hour |
| NO2, SO2, O3, CO | WHO AQG 2021, unchanged |

Other pollutants take the first worldwide row of the workbook, else the
first row.

## Run the import

You run the script on your computer, in `backend/`. It writes to the
database that the `.env` file names: `DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD` and `DB_NAME`.

1. To reach dev or prod, open a port-forward to its database. Use a local
   port other than 5432 (the local database) and 5433 (the test database).
2. Write a `.env` file for that database outside the repository. Set
   `DB_HOST=localhost` and `DB_PORT` to the local port of the
   port-forward. `dotenv run` overrides the shell, so a `DB_HOST=...`
   prefix on the command line has no effect.
3. Put the CSV at `data/benchmarks.csv` in the repository root. Both
   commands read this file. To read another file, add
   `csv=path/to/benchmarks.csv`.
4. Check the CSV against that database. This step writes nothing:

   ```sh
   make import-benchmarks-check env_path=path/to/dev.env
   ```

5. Write the references:

   ```sh
   make import-benchmarks env_path=path/to/dev.env
   ```

If `S3_PATH_PREFIX` in that file names production, the script refuses to
write. Add `ALLOW_PROD=1` to the command to write to production.

The import prints the number of references it wrote. The new references show in Explore at the next schema request, because the
catalog version changed.

## Backend

- `Benchmark` table: `id` becomes a text key. New columns: `period`,
  `institution`, `year`, `region`, `limit_type`, `legal_status`, `setting`,
  `qualifier`, `url`, `is_default`. `averaging` takes `hour`, `day` or
  `long_term`. The migration drops the table and creates it again, empty.
  Until the import runs on a database, Explore shows no reference there.
- The boot sync and the data upload mirror `parameters.csv` only. They
  never change the `benchmark` table.
- `/stats/schema`: each benchmark also carries `grain`, the query grain
  that matches its averaging (`hour`, `day` or `space`). The default comes
  first, then worldwide, then the other regions in alphabetical order.
- `/stats/measurements`: `grain=space` works for `stats` and `exceedance`.
  A time dimension at this grain answers 422.
- `/stats/relationships`: `grain=space` answers 422.

## Frontend

- `exploreStore.benchmarksOf` lists the references of a pollutant, and
  `defaultBenchmarkOf` gives its default. The store keeps no choice.
- `useFigureReference` holds the reference of one figure. The figure keeps
  one pick per pollutant, and a pollutant without a pick uses its default.
  The picks last as long as the page. After a reload, the defaults apply
  again.
- `ReferenceSource.vue`: one line under a figure that names the
  reference. It holds the label, the reference pill, the source name with
  an info icon, and a link to the source. If the name is too long for the
  card, the end is cut off. A tooltip on the name gives the full name, the
  institution, year, region, type of limit and period, and the note. With
  `compared`, the tooltip also says which means the figure compares with
  the reference: hourly, daily, or one per space.
- `ReferenceMenu.vue`: the small pill. It shows the value only, for
  example 1,200 ppm, so it never cuts text. The figure gives it the
  reference, and it sends a pick back to the figure. It has a red border and a
  short red line, the color of the reference line in the charts. This
  makes it different from the square menus in the card header. If a
  pollutant has one reference only, the pill does not open.
- The pill opens a menu in two steps. The menu first lists the regions,
  with the number of references in each. A click on a region shows the
  references of that region, with the default marked. A search lists the
  references of all regions, or of the open region. If every word of the
  search matches a reference, the menu keeps it.
- `DistributionFigure`, `PatternFigure`, `GroupFigure` and
  `RelationshipFigure` show the line under the chart. The charts module no
  longer holds a reference.

`DistributionFigure` and `PatternFigure` count the periods above the
reference, at the grain of the reference. When the user picks another
reference, they load again, and their tooltip shows the `compared` text.
`DistributionFigure` computes the levels and the shares at that grain.
`PatternFigure` keeps daily levels, and only the shares follow the grain.
If the reference changes, it keeps the drilled month. Above a long-term
reference, it shows no monthly share, and the strip title says why.

`GroupFigure` and `RelationshipFigure` only draw the reference line, so a
new pick redraws them without a request. They plot daily means and means
per space, so their tooltip has no `compared` text.

## Out of scope

- A country filter for the reference menu (jfr1993 on #202).
- The other tasks of #232: sample sizes, monthly pattern, exceedance by
  segment, link to the IEQ guidelines database and DALY.
- An outdoor CO2 measurement per study. The 400 ppm level is a constant.

## Tests

- `test_benchmarks.py`: one default per pollutant, unknown averaging and
  duplicate ids fail. A replace writes only a change.
- `test_parameters.py`: the boot sync keeps the imported references.
- `test_import_benchmarks.py`: the import writes a CSV to the test
  database. A check writes nothing, a refused CSV keeps the current
  references, and a production target needs `--allow-prod`.
- `test_stats_measurements.py`: `grain=space` gives one value per space,
  exceedance counts spaces, a time dimension answers 422.
- `test_stats_schema.py`: the benchmark fields and the default order.

The frontend has no test runner. `vue-tsc` and ESLint pass on the changed
files. Nobody checked the figures in a browser yet.
