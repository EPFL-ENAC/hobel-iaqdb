---
status: draft
issue: 129
last_updated: 2026-09-22
summary: Three query-shaped stats endpoints over raw measurements in a TimescaleDB hypertable (continuous aggregates as a derived cache), one response envelope, and a click model where every drill-down is a filter refinement of the same request. Implemented on branch feat/129; §15 lists where the code refined the design.
---

# Explore charts API

Design note for issue #129. Flip `status` to `accepted` when the issue is
closed; chart sub-issues #109–#126 implement against this contract.
All four tiers of §13 are implemented; §15 records what the code does
differently from the first draft and why.

## 1. Facts this design rests on

Everything below was read from the code and the seed data, not assumed.

- **Metadata** lives in Postgres: `study → building → space`, `study →
  instrument`, `study → dataset → variable` (`api/models/catalog.py`). Filters
  are the enacit4r-sql JSON dialect (`$and`, `$gte`, nested `$study`,
  `$building`, `$space` joins) shared by `/catalog/*` and `/stats/frequencies/*`.
- **Measurements** are not in Postgres today. The seed script on branch
  `feat/128-seed-bulk-import-studies` uploads processed CSVs to the study
  folder on S3; S3 stays the archive of record for the files, Postgres
  becomes the queryable copy (§3). Every processed CSV is already in one **long schema**, 27
  columns, the ones that matter being:
  `dataset_id, data_type, building_id, space_id, instrument_id, timestamp,
  start_timestamp, end_timestamp, parameter, statistic, value, real_unit,
  inferred_unit, value_qualifier`.
  `data_type ∈ {time_series, time_integrated, statistical}`. `parameter` is a
  snake_case slug (`co2`, `pm2_5`, `air_temperature`), distinct from the
  `Variable.reference` taxonomy (`carbon dioxide`, `particle mass
  concentration`). Timestamps are naive local wall-clock.
- **Volume** (SEED_DATA, 87 studies, 1 314 long-format CSVs; 64 studies
  ship them at the top level, 22 under `source_packages/`, 1 both):

  | quantity | value |
  | --- | --- |
  | CSV size | 91 GB |
  | bytes per CSV row | 265–300 |
  | raw records | ~305 M |
  | median / p90 / max file | 12 MB / 152 MB / 7.9 GB |
  | hourly rows per raw row (5-min sensors) | 1 / 12 |
  | hourly rows per raw row (1-s sensors) | 1 / 3 500 |
  | TimescaleDB compression (segment by dataset, space, parameter) | 31× |

  Measured on a 5 M-row sample from `D1053` (TimescaleDB 2.28 on PG 15,
  Docker Desktop, 4 CPU / 4 GB): raw rows compress to ~20 bytes each, so the
  whole seed is **~6 GB compressed** and **~140 GB uncompressed at the peak of
  the load**. Hourly continuous aggregates are 5–20 M rows, daily 0.3–1 M.
  An hourly `GROUP BY` over 5 M compressed raw rows takes ~0.5 s, which is
  why charts read the continuous aggregates and raw is reserved for narrow
  filters (§4, `grain=raw`).
- **Frontend**: filters are one Pinia store (`stores/filters.ts`); the catalog
  store derives entity-specific filter JSON from it. Charts are ECharts via
  `vue-echarts`; the two existing metadata charts in `PlotsDrawer.vue` count
  map features client-side, which violates "backend is the source of truth"
  and will be moved onto the metadata endpoint below.

## 2. Decisions

| # | Decision | Why |
| --- | --- | --- |
| D1 | **Three routes, one per query shape**, not per chart: `/stats/metadata`, `/stats/measurements`, `/stats/relationships`, plus a static `/stats/schema` descriptor. | 18 charts collapse into three SQL shapes: group-by over catalog rows, group-by over measurements, and pairwise join over measurements. A route per chart would re-implement filters 18 times; a single route would branch on chart type inside the handler. |
| D2 | **Raw measurements in a TimescaleDB hypertable** (compressed), loaded at seed and at publish. Hourly and daily **continuous aggregates** are a derived cache the database maintains, never a second source of truth. No S3 read on any request path. | Pre-aggregating only freezes the filter vocabulary at import time: value-based filters (readings above a threshold), `value_qualifier`/`statistic` filters, non-hour windows (WHO 8-h means) and cross-parameter conditions at raw resolution are all lost once rows collapse to hourly means. With raw rows in the database any future filter is a `WHERE` clause. Continuous aggregates give the same hourly/daily speed as hand-built rollup tables, are always consistent with raw, and cost nothing to maintain in application code. TimescaleDB is a Postgres extension, so asyncpg, SQLModel and Alembic are unchanged. |
| D3 | **One response envelope** `{ meta, buckets[] }` for all three routes. Empty is `buckets: []` with `meta.n = 0` and `meta.available_parameters` filled. | `charts.ts` maps buckets to ECharts series generically. The UI gets both the "no data" signal and what to suggest instead. |
| D4 | **A click is a filter refinement of the same request, never a new endpoint.** Buckets carry the dimension key; the schema descriptor says how a key becomes a filter criterion and which dimension to drill into next. | Drill-downs reuse the cache, the filter contract, and the chart component. Adding a drill level is data in the dimension registry, not code. |
| D5 | **Parallel GETs for visible charts, no batch endpoint.** | GET keeps per-query HTTP caching and lets drill-downs share entries with their parents. Batching would couple a 5 ms metadata chart to a 200 ms relationship chart and defeat caching. |
| D6 | **Delete `/stats/frequencies/*`** in the PR that ships `/stats/metadata`. | Same contract, strictly more capable. No dual paths. |

## 3. Storage: hypertable and continuous aggregates

One fact table and three small dictionary/summary tables, all created by an
Alembic migration that also runs `CREATE EXTENSION IF NOT EXISTS timescaledb`.

```
parameter            slug PK, label, reference (taxonomy), unit (canonical), conversions JSONB
benchmark            id PK, parameter FK, source, averaging (hour|day), value, unit, note
dataset_parameter    dataset_id FK, parameter FK, unit, n_records, n_missing, n_unlinked,
                     n_statistical, first_at, last_at, n_buildings, n_spaces   PK(dataset_id, parameter)

measurement          -- TimescaleDB hypertable, chunk_time_interval = 1 month
                     dataset_id FK, study_id FK, building_id FK?, space_id FK?, instrument_id FK?,
                     parameter FK, data_type, statistic, ts TIMESTAMP (local wall-clock),
                     start_ts?, end_ts?, value DOUBLE PRECISION, value_qualifier?
                     compress: segmentby (dataset_id, space_id, parameter), orderby ts DESC

measurement_hour     continuous aggregate over measurement WHERE data_type <> 'statistical':
                     dataset_id, study_id, building_id, space_id, instrument_id, parameter,
                     hour = time_bucket('1 hour', ts), n, mean, min, max
measurement_day      hierarchical continuous aggregate over measurement_hour:
                     same keys, day = time_bucket('1 day', hour), n = sum(n),
                     mean = sum(mean·n)/sum(n), min, max
```

Rules, all explicit and all reported by `make seed-check`:

- `parameter` is seeded from versioned CSVs (`api/data/parameters.csv` and
  `api/data/benchmarks.csv`, mirrored into the tables by
  `ParameterService.sync` at boot and at seed). The content shipped here is
  **provisional**, derived from the slugs and units present in SEED_DATA and
  the factors of `Dictionary_data.xlsx`; #107 replaces it as data. No
  guessing units: `value` is stored in the canonical unit, the source unit
  is `coalesce(real_unit, inferred_unit)` (the processed CSVs leave
  `real_unit` empty for 17 % of the rows and fill `inferred_unit`), the
  conversion is in the dictionary.
- **Every row goes to exactly one bin** of the dataset's `load_report`
  (`loaded`, `missing`, `statistical`, `unknown_parameter{slug}`,
  `unknown_unit{slug|unit}`, `unparseable_value{slug}`,
  `unparseable_timestamp`, plus `unlinked_building/space/instrument`
  counts). Rejected rows are counted, never fixed and never loaded; the
  dataset fails only when no row loads or a file cannot be read. The seed
  data has 14 000 distinct slugs, 14 M non-numeric values and 740 k
  unparseable timestamps, so "an unknown slug fails the dataset" would have
  loaded nothing. `missing` is a value that is empty or `NA`; a decimal
  comma (`18,9`) is accepted, `5.2 K` is not.
- `time_integrated` rows keep `start_ts` and `end_ts` and take
  `ts = coalesce(start_ts, ts)`. `statistical` rows carry no timestamp in
  99.97 % of the cases, so they **cannot enter the hypertable**: they are
  counted in the report only, until #127 gives them a table.
- `building_id` / `space_id` / `instrument_id` are resolved to catalog FKs by
  identifier within the study (spaces within their building). Unresolved
  rows keep `NULL` FKs, are counted in the report, and appear as a `null`
  bucket when grouped by a building/space attribute. The UI labels that
  bucket "unknown"; it is never merged into another bucket.
- `ts` is local wall-clock, stored as `TIMESTAMP` without time zone. A
  trailing UTC offset (`-04:00`, 26 M rows in 9 datasets) is **dropped**, the
  wall clock is kept. Month-of-year and hour-of-day profiles are only
  meaningful in local time.
- The continuous aggregates are **materialized only** (`materialized_only =
  true`): a request never triggers real-time aggregation over raw. They are
  refreshed by `MeasurementService.refresh_all()` (full window; TimescaleDB
  only recomputes invalidated buckets) at the end of each load and after
  every delete that cascades into `measurement`, so a chart is either up to
  date or the dataset is still `pending`. No background refresh policy.
- `dataset_parameter` is derived from `measurement` in one SQL statement per
  load (`n_records`, `n_missing`, `first_at`, `last_at`, `n_buildings`,
  `n_spaces`); it is the only place counts of raw records are cached.
- Every table has `ON DELETE CASCADE` from `dataset`. `dataset_id` is a
  compression segment-by column, so deleting a dataset drops whole compressed
  batches instead of decompressing rows.

Indexes on `measurement`: `(parameter, ts DESC)`, `(dataset_id, parameter,
ts DESC)`, `(space_id, ts DESC)`; the same three on each continuous
aggregate with `hour` / `day`. Building and space attribute filters join the
small catalog tables; the fact scan is bounded by `(parameter, time range)`,
and on compressed chunks by the segment-by columns.

### Import pipeline

`MeasurementService.load(dataset_id, paths)`:

1. DuckDB reads each CSV (`read_csv`, streaming, bounded memory: the 7.9 GB
   file must not be loaded with pandas), validates slugs and units against
   the dictionary, converts values to the canonical unit, resolves catalog
   FKs, and yields Arrow batches. Measured parse rate on the seed files:
   1.5–3.7 GB/s.
2. Batches go straight into `measurement` with asyncpg
   `copy_records_to_table`. No intermediate CSV.
3. After the rows are in: `compress_chunk(if_not_compressed => true)` on
   every chunk the dataset touched (TimescaleDB 2.28 recompresses partially
   compressed chunks in place), `refresh_continuous_aggregate` on
   `measurement_hour` then `measurement_day` for
   `[first_at, last_at + 1 day)`, and the `dataset_parameter` upsert, all in
   the same job.
4. The whole load is idempotent per dataset: it starts by deleting the
   dataset's rows. The MD5 key from #128 only skips the S3 upload:
   `StudyService.save` recreates the study and its datasets, so the seed
   always reloads measurements.
5. Seed calls it per dataset after the S3 upload. Publish (`/contribute`)
   calls it as a background task, streaming the S3 object to a temp file
   first. `dataset.summary_status ∈ {pending, ready, failed}`,
   `summary_error` and `load_report` make the state visible in the UI; a
   failed load is never a silent empty chart.

Seed-only optimisations, applied by the seed script and not by publish: drop
the three secondary indexes on `measurement` before the bulk load and rebuild
them after (halves the `COPY` time), and set `synchronous_commit = off` and a
large `max_wal_size` for the duration of the run. Publish loads one dataset
into an indexed table and takes seconds.

Measured cost of loading the full seed (5 M-row sample, scaled to ~305 M
rows; Docker Desktop on a laptop, 4 CPU / 4 GB / virtual disk):

| step | time |
| --- | --- |
| parse CSVs (DuckDB) | ~6 min |
| `COPY` into hypertable, no indexes | ~14 min |
| build 3 indexes | ~7 min |
| compress chunks | ~33 min |
| refresh continuous aggregates | ~2 min |
| **total, one-time** | **~1 h laptop, ~30–40 min on a server with local NVMe** |

The bottleneck is disk write throughput, not CPU: four parallel `COPY`
streams gained 7 % over one. A GPU is irrelevant. The seed already spends
2+ h uploading the same files to S3, so the end-to-end seed becomes ~3 h.

Disk: datasets overlap in time, so a monthly chunk can only be compressed
once every dataset touching it is loaded. The seed loads everything and
compresses in one pass at the end, which needs **~140 GB free** on the
database host during the seed; the steady-state size is **~6 GB**. Publish
loads one dataset at a time and recompresses its chunks immediately, so it
never needs that headroom.

Deployment: the `postgres` service in `docker-compose.yml` moves from
`postgres:15.5-alpine` to `timescale/timescaledb:latest-pg15`. The production
database host must allow the `timescaledb` extension (open point, §14).

## 4. Common parameter contract

Every route accepts the same parameters, parsed once into an `ExploreQuery`
model (`Annotated[ExploreQuery, Query()]`), so validation and OpenAPI docs are
shared.

| param | type | semantics |
| --- | --- | --- |
| `filter` | JSON string | Same dialect and nesting as `/catalog/*`: `{ ...study criteria, "$building": {...}, "$space": {...}, "$dataset": {...} }`. Measurement routes resolve nested keys to joins on the measurement table or continuous aggregate; the metadata route anchors on `entity`. Built on the frontend by **one** function in `api/explore.ts` from the filters store, so map, lists and charts agree. |
| `from`, `to` | ISO date | Half-open `[from, to)` on the time column of the chosen grain. Dates, not datetimes: charts pick years and months, and day-granular keys keep cache keys stable. |
| `parameters` | comma-separated slugs | From `parameter.slug`. Unknown slug → 422 listing valid slugs. Max 10. |
| `by` | comma-separated dimension keys, max 2 | From the dimension registry (§5). Time bucketing is a dimension (`month`, `year`), so there is no separate `bucket` parameter. Second key gives stacked/heatmap series. |
| `agg` | enum per route | metadata: `count`, `availability`. measurements: `coverage`, `count`, `stats`, `exceedance`. relationships: `pairs`, `matrix`. |
| `grain` | `day` (default), `hour` or `raw` | Which table the statistic is computed over: `measurement_day`, `measurement_hour` or the raw `measurement` hypertable. At `day`/`hour`, percentiles are percentiles of bucket means; at `raw` they are percentiles of the readings themselves. The response echoes the grain so the label is honest. `raw` is accepted only when `dataset_parameter` says the filter covers **≤ 20 M raw records**; above that the route answers 422 with the matched count and the client falls back to `hour`. No silent downgrade. |
| `qualifier` | comma-separated | `grain=raw` only. Keeps rows whose `value_qualifier` is in the list; default is all. |
| `threshold` | float | `agg=exceedance` only. The UI takes it from a benchmark in `/stats/schema` or from user input; the server never invents one. |
| `entity` | `studies\|buildings\|spaces\|datasets` | metadata route only. |
| `fields` | comma-separated | `agg=availability` only; defaults to all nullable fields of the entity. |
| `x`, `y` | slug or metric key | relationships `agg=pairs`. A metric key is a numeric catalog column from a closed list (`space.occupancy_density`, `space.occupancy_number`, `space.floor_area`, `space.space_volume`, `building.airtightness`, `building.construction_year`, `building.altitude`). |
| `method` | `pearson` (default) or `spearman` | relationships only. |

Canonical form: the frontend sorts list values and serialises the filter with
sorted keys and no `undefined` entries. The backend re-canonicalises before
hashing so the server cache and the browser cache hit on the same key.

## 5. Dimension registry (`GET /stats/schema`)

One static, long-cached call at page load returns the dimensions, the
parameter dictionary with benchmarks, and the catalog version.

| key | source | `filter_path` | `drill_to` |
| --- | --- | --- | --- |
| `study` | `study.identifier` | `identifier` | `dataset` |
| `dataset` | `dataset.id` | `$dataset.id` | — |
| `country` | `building.country` | `$building.country` | `city` |
| `city` | `building.city` | `$building.city` | `study` |
| `climate_zone` | `building.climate_zone` | `$building.climate_zone` | `country` |
| `building_type` | `building.type` | `$building.type` | `country` |
| `ventilation` | `building.mechanical_ventilation` | `$building.mechanical_ventilation` | `ventilation_type` |
| `ventilation_type` | `space.mechanical_ventilation_type` | `$space.mechanical_ventilation_type` | `space_type` |
| `space_type` | `space.type` | `$space.type` | — |
| `occupancy` | `space.occupancy` | `$space.occupancy` | — |
| `parameter` | `measurement.parameter` | `parameters` | — |
| `year` | `date_trunc('year')` | `from`/`to` | `month` |
| `month` | `date_trunc('month')` | `from`/`to` | `day` |
| `day` | `date_trunc('day')` | `from`/`to` | — |
| `month_of_year` | `extract(month)` | — | — |
| `hour_of_day` | `extract(hour)`, requires `grain=hour` | — | — |

The registry is a Python dict `key → (column expression, filter_path,
drill_to)` in `api/services/explore/dimensions.py`. Adding a dimension is one
line there and nothing on the frontend.

## 6. Response envelope

```jsonc
{
  "meta": {
    "source": "measurements",           // metadata | measurements | relationships
    "agg": "stats",
    "grain": "day",
    "dimensions": ["country"],          // order of entries in bucket.key
    "parameters": ["co2"],
    "unit": "ppm",                      // null when parameters differ in unit
    "from": "2012-01-01", "to": "2013-01-01",
    "n": 18342,                         // grain-level observations matched
    "n_records": 5320011,               // raw records behind them
    "version": 42,                      // catalog version the result was computed on
    "available_parameters": null        // filled only when buckets is empty
  },
  "buckets": [
    { "key": ["CH"], "n": 4021, "n_records": 1200034,
      "stats": { "mean": 812.4, "sd": 210.1, "min": 401, "p05": 480, "p25": 640,
                 "p50": 790, "p75": 950, "p95": 1290, "max": 2410 } }
  ]
}
```

- `key` has one entry per dimension, as strings (`"CH"`, `"2012-03-01"`,
  `"3"` for month-of-year) or `null` for unknown. The frontend formats.
- Per-aggregation payloads are optional fields on the bucket and the route
  is declared with `response_model_exclude_none=True`, so a `count` bucket is
  just `{key, n, n_records}`.
- **Empty state**: `buckets: []`, `meta.n: 0`, and `meta.available_parameters`
  lists the slugs that do have data under the same `filter`/`from`/`to`
  (one query on `dataset_parameter`, run only on the empty path). The UI
  message is "No PM2.5 data for these filters. Available: CO2, temperature."
  No `empty` flag: `n == 0` is the flag, and an empty array is what every chart
  needs to clear itself.
- Buckets are ordered deterministically: time dimensions ascending, category
  dimensions by `n` descending then key. Same input, same order, every time.

## 7. The three routes

### `GET /stats/metadata`

Group-by over catalog rows. `agg=count` counts distinct entities per key;
`agg=availability` returns per field `{present, total}`.

```
/stats/metadata?entity=datasets&by=country&parameters=co2&filter=...
→ datasets per country that contain CO2   (joins dataset_parameter)
/stats/metadata?entity=buildings&agg=availability&fields=climate_zone,timezone,construction_year
→ buckets keyed by field name with availability {present, total}
```

Runs on tables of a few thousand rows; target < 20 ms locally.

### `GET /stats/measurements`

Group-by over `measurement_day`, `measurement_hour` or `measurement`
(`grain`), joined to `dataset`, `building`, `space` as the filter and
dimensions require. At `grain=raw` the same SQL runs over the hypertable,
`n` counts readings, and `n_records = n`.

| agg | payload | SQL core |
| --- | --- | --- |
| `coverage` | `coverage {n_datasets, n_missing, first_at, last_at}` | reads `dataset_parameter` only, no fact scan. Building and space dimensions join through the study, so a dataset counts under every country its study has a building in |
| `count` | `n`, `n_records` | `count(*)`, `sum(n)` |
| `stats` | `stats {…}` | `percentile_cont(array[.05,.25,.5,.75,.95]) within group (order by mean)`, weighted mean, `stddev_samp(mean)`, `min(mean)`, `max(mean)` (the same series as the percentiles, so box plots are consistent) |
| `exceedance` | `exceedance {threshold, n_above, share}` | `count(*) filter (where mean > :threshold)` |

`by=parameter&agg=coverage` is also the query behind the dynamic variable
selector (#108): it lists what exists under the current filter, in one call,
without a dedicated route.

### `GET /stats/relationships`

Pairwise queries over `measurement_hour` (`grain=hour` default here, because
co-variation is an hourly phenomenon; `grain=day` allowed; `grain=raw` allowed
under the same 20 M-record cap, joining on `(dataset_id, space_id,
instrument_id, ts)` so only co-located, co-timed readings pair).

- `agg=pairs&x=co2&y=air_temperature[&by=country]`: self-join on
  `(dataset_id, space_id, hour)`. Two statements: (1) per group
  `count, regr_slope, regr_intercept, regr_r2, corr` over **all** matched rows;
  (2) a deterministic sample of points, `row_number() over (order by
  dataset_id, space_id, hour) % step = 0` with `step = ceil(n / 2000)` (the
  aggregates have no `id`), so the trend line is exact and the dots are a
  stable, cacheable sample. Bucket carries `fit`, `points`, `n` and
  `sampled` (true only when `step > 1`).
- `x` parameter with a metric `y` (chart 13, CO2 × occupancy): `x` is first
  aggregated per `(dataset, space)`, then joined to the space column; one point
  per space, `fit` over all spaces. `meta.grain` echoes `space`.
- `agg=matrix&parameters=co2,pm2_5,tvoc[&method=spearman]`: **one scan**.
  A CTE pivots the filtered rows to one column per parameter
  (`max(mean) filter (where parameter = 'co2') as co2 …` grouped by
  `dataset_id, space_id, hour`), then a single `SELECT` computes
  `corr(a, b)` and `count(a) filter (where b is not null)` for every pair.
  Spearman ranks each column, per pair, within the rows where the other
  parameter is present (`rank() over (partition by b is not null order by
  a)`, ties get their lowest rank). Cells are buckets keyed `[x, y]` (slugs
  sorted) with `n` and `fit.r`. Max 10 parameters (45 cells).

## 8. Click model

Every click on a chart is one of three declared kinds, handled by a single
`onBucketClick(chart, bucket)` in `charts.ts`:

| kind | what happens | network |
| --- | --- | --- |
| `filter` | `dimension.filter_path` + `bucket.key` are pushed into the global filters store. Every chart, the map and the lists re-query. | same routes, new keys |
| `drill` | The chart keeps a local stack. It merges the criterion into its own filter copy and re-queries with `by = dimension.drill_to`. Breadcrumb pops the stack; popped levels are served from the client cache, no refetch. | same route, one request |
| `navigate` | Opens the existing catalog view for the bucket (`/catalog/datasets?filter=…`, `/study/:id`), merged filter carried in the URL. | existing endpoints |

Because a drill-down is the parent request plus one criterion and a different
`by`, the server cache key of the parent stays warm and the child is a ~10 ms
query on an already-filtered index range. Nothing about a click is
chart-specific except the declared kind and, for chart 17 → 18, that a cell
click sets `x`, `y` on the pairs chart.

## 9. Performance and caching

### Budgets (local, p95 under a typical filter; deployed ≈ 4× slower)

| route | local | deployed |
| --- | --- | --- |
| `/stats/schema` | < 5 ms (in-process cache) | < 20 ms |
| `/stats/metadata`, `measurements agg=coverage` | < 20 ms | < 100 ms |
| `/stats/measurements grain=day` | < 60 ms | < 300 ms |
| `/stats/measurements grain=hour` | < 150 ms | < 600 ms |
| `/stats/measurements grain=raw` (≤ 20 M records) | < 500 ms | < 2 s |
| `/stats/relationships` | < 200 ms | < 800 ms |

Page goal from the conventions is < 400 ms deployed. The metadata family
(charts 1–8) meets it on first paint; hour-grain and relationship charts are
below the fold or behind a tab and load while the user reads. Raw-grain
queries are opt-in, capped, and never on first paint. If hour-grain queries
exceed budget on real volume, the escape hatch is a `measurement_month`
continuous aggregate behind the same contract; no API change.

### Cache layers

1. **HTTP**: `Cache-Control: private, max-age=300` and a strong `ETag =
   sha1(route + canonical query + catalog_version)`. Re-opening a chart or
   popping a drill level is a 304 at worst.
2. **Server**: `cachetools.TTLCache(maxsize=1024, ttl=600)` keyed by the same
   triple, with a per-key `asyncio.Lock` so identical concurrent requests
   collapse into one query.
3. **Client**: `useExploreQuery(params)` composable keeps a `Map<canonical key,
   result>` for the page session, dedupes in-flight promises, and aborts the
   previous request when its params change so a stale response never paints.

`catalog_version` is a single-row table bumped **in the route transaction** of
publish, delete and seed. Reading it is one PK lookup per request. Nothing is
ever invalidated by hand, and no result can outlive the data it was computed
on.

### Request scheduling on the Explore page

- Charts mount lazily (`v-intersection`); a filter change re-queries only
  visible charts, others re-query when scrolled into view.
- Filter edits are debounced 250 ms; parameter selection is applied on change.
- Requests run in parallel over HTTP/2 through Traefik. The asyncpg pool must
  cover the concurrent chart count: `create_async_engine(pool_size=20,
  max_overflow=10)`. Side finding: `api/db.py` runs with `echo=True`, which
  logs every statement in production and must be turned off in the same PR.
- Render order needs no orchestration: metadata answers arrive first because
  they are cheapest.

## 10. Mapping table: chart → request → click

`F` = global filter, `P` = selected parameters, `T` = `from`/`to`. All requests
also carry `filter=F` unless stated.

| # | Chart | Route and parameters | Click |
| --- | --- | --- | --- |
| 1 | Datasets by country | `metadata?entity=datasets&by=country&parameters=P` | drill → `city` → `study`; second level `navigate` to datasets list |
| 2 | Records by pollutant | `measurements?agg=coverage&by=parameter` | `filter`: sets `P` (this chart *is* the variable selector's data) |
| 3 | Datasets by building type | `metadata?entity=datasets&by=building_type&parameters=P` | `filter` |
| 4 | Datasets by ventilation | `metadata?entity=datasets&by=ventilation` | drill → `ventilation_type` (space level) |
| 5 | Datasets by climate zone | `metadata?entity=datasets&by=climate_zone` | drill → `country`. Zero-count zones are rendered by merging with the known Köppen domain on the client (presentation, no computation) |
| 6 | Records by month | `measurements?agg=count&by=month_of_year,parameter&grain=day&from=T&to=T` | tooltip shows the parameter stack; no drill |
| 7 | Measurement period | `measurements?agg=coverage&by=dataset` → `first_at`/`last_at` Gantt | `navigate` → study page |
| 8 | Metadata availability | `metadata?entity=buildings&agg=availability` and `entity=spaces` | `navigate` → catalog list filtered to missing values (needs a null criterion in the QueryBuilder; verify enacit4r-sql supports it before promising the click) |
| 9 | Descriptive statistics | `measurements?agg=stats&parameters=P&by=<context>&grain=day&from=T&to=T` box plot | drill along the context's `drill_to` |
| 10 | Benchmark comparison | same as 9 with `by=year`; benchmark line from `/stats/schema` | toggles benchmark; `agg=exceedance&threshold=<benchmark.value>` for the share above |
| 11 | Trends | `measurements?agg=stats&parameters=P&by=month&from=Y-01-01&to=Y+1-01-01` → line (p50, p25–p75 band) and table from the same buckets | drill → `day` inside the clicked month |
| 12 | Exceedance over time | `measurements?agg=exceedance&threshold=…&by=month_of_year&grain=<benchmark.averaging>` | drill → `year` |
| 13 | CO₂ × occupancy | `relationships?agg=pairs&x=co2&y=space.occupancy_density` | `navigate` → space |
| 14 | CO₂ × ventilation | `measurements?agg=stats&parameters=co2&by=ventilation_type` | drill → `space_type` |
| 15 | Pollutant × climate | `measurements?agg=stats&parameters=P&by=climate_zone` | drill → `country` |
| 16 | Pollutant × building type | `measurements?agg=stats&parameters=P&by=building_type` | drill → `country` |
| 17 | Correlation matrix | `relationships?agg=matrix&parameters=P&method=…` | cell click opens chart 18 with `x`, `y` from the cell key |
| 18 | Custom relationship | `relationships?agg=pairs&x=…&y=…[&by=…]` | `navigate` → entity behind the point |

Benchmarks (chart 10, 12): the `benchmark` table is seeded with WHO 2021 air
quality guideline values (PM2.5 24-h 15 µg/m³, PM10 24-h 45, NO2 24-h 25,
O3 8-h 100, CO 24-h 4 mg/m³) marked `source = "WHO AQG 2021"`, replaceable by
the domain expert's values as data. No random placeholder in code.

## 11. Pydantic stubs (`api/models/explore.py`)

```python
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Entity = Literal["studies", "buildings", "spaces", "datasets"]
Grain = Literal["day", "hour", "raw"]
Source = Literal["metadata", "measurements", "relationships"]
MetadataAgg = Literal["count", "availability"]
MeasurementAgg = Literal["coverage", "count", "stats", "exceedance"]
RelationshipAgg = Literal["pairs", "matrix"]
Method = Literal["pearson", "spearman"]
Agg = MetadataAgg | MeasurementAgg | RelationshipAgg


# ---- /stats/schema -------------------------------------------------------


class Dimension(BaseModel):
    key: str
    label: str
    entity: Literal["study", "building", "space", "dataset", "parameter", "time"]
    filter_path: str | None
    drill_to: str | None
    kind: Literal["category", "time"]


class Benchmark(BaseModel):
    id: int
    parameter: str
    source: str
    averaging: Grain
    value: float
    unit: str
    note: str | None = None


class Parameter(BaseModel):
    slug: str
    label: str
    reference: str
    unit: str
    benchmarks: list[Benchmark] = Field(default_factory=list)


class ExploreSchema(BaseModel):
    dimensions: list[Dimension]
    parameters: list[Parameter]
    metrics: list[str]
    version: int


# ---- query ---------------------------------------------------------------


class ExploreQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    filter: str | None = None
    from_: date | None = Field(default=None, alias="from")
    to: date | None = None
    parameters: list[str] = Field(default_factory=list, max_length=10)
    by: list[str] = Field(default_factory=list, max_length=2)
    grain: Grain = "day"
    qualifier: list[str] = Field(default_factory=list)
    threshold: float | None = None
    entity: Entity | None = None
    fields: list[str] = Field(default_factory=list)
    x: str | None = None
    y: str | None = None
    method: Method = "pearson"

    @field_validator("parameters", "fields", "qualifier", mode="before")
    @classmethod
    def split_sorted(cls, value: str | list[str]) -> list[str]:
        items = value.split(",") if isinstance(value, str) else value
        return sorted({v for v in items if v})

    @field_validator("by", mode="before")
    @classmethod
    def split_ordered(cls, value: str | list[str]) -> list[str]:
        # order matters: it is the order of entries in bucket.key
        items = value.split(",") if isinstance(value, str) else value
        return list(dict.fromkeys(v for v in items if v))


# ---- envelope ------------------------------------------------------------


class Stats(BaseModel):
    mean: float
    sd: float | None
    min: float
    p05: float
    p25: float
    p50: float
    p75: float
    p95: float
    max: float


class Exceedance(BaseModel):
    threshold: float
    n_above: int
    share: float


class Coverage(BaseModel):
    n_datasets: int
    n_missing: int
    first_at: datetime | None
    last_at: datetime | None


class Availability(BaseModel):
    present: int
    total: int


class Fit(BaseModel):
    slope: float | None
    intercept: float | None
    r2: float | None
    r: float | None


class Bucket(BaseModel):
    key: list[str | None]
    n: int
    n_records: int | None = None
    stats: Stats | None = None
    exceedance: Exceedance | None = None
    coverage: Coverage | None = None
    availability: Availability | None = None
    fit: Fit | None = None
    points: list[tuple[float, float]] | None = None
    sampled: bool | None = None


class Meta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: Source
    agg: Agg
    grain: Grain | Literal["space", "entity"]
    dimensions: list[str]
    parameters: list[str]
    unit: str | None
    from_: date | None = Field(default=None, alias="from")
    to: date | None
    n: int
    n_records: int | None = None
    version: int
    available_parameters: list[str] | None = None


class ExploreResult(BaseModel):
    meta: Meta
    buckets: list[Bucket]
```

Routes are declared `response_model=ExploreResult,
response_model_exclude_none=True`; `from` survives as a query and JSON key
through the alias, and responses are serialised `by_alias=True`.

Frontend types in `models.ts` mirror these one to one; `charts.ts` gains
`toSeries(result, dimensionIndex)` and `onBucketClick(chart, bucket)`.

## 12. Frequencies endpoints

Deleted in the PR that adds `/stats/metadata`. Migration is mechanical:

| old | new |
| --- | --- |
| `/stats/frequencies/studies?by=X` | `/stats/metadata?entity=studies&by=X` |
| `/stats/frequencies/buildings?by=X` | `/stats/metadata?entity=buildings&by=X` |
| `/stats/frequencies/spaces?by=X` | `/stats/metadata?entity=spaces&by=X` |

`GroupByResult`/`GroupByCount` are removed with them. The three catalog-store
functions `countStudies/countBuildings/countSpaces` become one `metadata()`
call in `api/explore.ts`, and the two `PlotsDrawer` charts that count map
features client-side switch to it, so the drawer, the map and the Explore page
show the same numbers from the same query.

## 13. Implementation order

Each tier is a shippable PR against `dev` with its own plan file.

1. **Hypertable** (#128 follow-up): TimescaleDB image in `docker-compose.yml`,
   migration with the extension, `parameter`, `benchmark`,
   `dataset_parameter`, `measurement` hypertable with compression,
   `measurement_hour` / `measurement_day` continuous aggregates,
   `catalog_version`; `MeasurementService`; seed and publish integration.
2. **Contract**: `api/models/explore.py`, `ExploreQuery`, dimension registry,
   `/stats/schema`, `/stats/metadata`, cache layer, delete frequencies,
   frontend `api/explore.ts` + `useExploreQuery` + `charts.ts` helpers.
   Unblocks charts 1, 3, 4, 5, 8.
3. **Measurements**: `/stats/measurements` with the four aggregations.
   Unblocks charts 2, 6, 7, 9, 10, 11, 12, 14, 15, 16.
4. **Relationships**: `/stats/relationships`. Unblocks 13, 17, 18.

Each tier ships a test per aggregation on a fixture of ~5 000 raw rows with a
known answer (`backend/tests/fixtures.py`, expectations recomputed in plain
Python in `tests/expected.py`), run at all three grains so the continuous
aggregates are checked against raw, and a query-plan check (`EXPLAIN`)
asserting the fact scan uses an index starting with `parameter`. Tests run
against the TimescaleDB image, not plain Postgres: `make test-db` starts a
throwaway container on port 5433, `make test` runs the suite against it
(the tests truncate tables and refuse any other port). CI runs the same
against a `timescale/timescaledb:latest-pg15` service.

## 14. Out of scope and open points

- Per-request reads of S3 (pandas/pyarrow/DuckDB on the request path) are
  rejected, not deferred: they cannot meet the budget and would make response
  time depend on file size chosen by contributors.
- The parameter dictionary content is #107's deliverable; this design only
  fixes its shape and that unknown slugs fail loudly.
- Time-integrated and statistical `data_type` handling above is the minimal
  explicit rule; #127 may refine it, behind the same tables.
- The null-criterion needed for chart 8's click has to be confirmed in
  enacit4r-sql `QueryBuilder` before the sub-issue promises it.
- The production database host has to allow the `timescaledb` extension and
  provide ~140 GB of temporary disk for the one-time seed. To confirm with
  the hosting team before tier 1 starts.
- The 20 M-record cap on `grain=raw` is a first value from the 0.5 s / 5 M
  rows measurement; tune it against the deployed budget once tier 3 runs on
  real volume. The cap is checked on `dataset_parameter` for the matched
  studies and datasets (building and space criteria cannot narrow it there),
  so it is conservative.
- The processed CSVs use 14 000 free-form slugs (`temperature_c`,
  `avp_in1_co2`, `carbon_dioxidee` …); canonicalising them is #107's job.
  Until then the report of every dataset lists what was left out.

## 15. What the implementation refined

Read with §1–§14; code wins where they still disagree.

| topic | first draft | shipped |
| --- | --- | --- |
| unknown slug or unit | fails the dataset | row counted in `load_report`, dataset fails only when nothing loads (§3) |
| `statistical` rows | loaded, excluded from aggregates | not loaded (no timestamp), counted in the report (§3) |
| source unit | `real_unit` | `coalesce(real_unit, inferred_unit)` (§3) |
| tz offsets | not considered | stripped, wall clock kept (§3) |
| aggregate refresh | per dataset time range | `refresh_all()` after loads and deletes; invalidation makes it cheap (§3) |
| `dataset_parameter` | also `n_unlinked`, `n_statistical` | those live in `dataset.load_report` |
| seed skip | MD5 skips the load too | MD5 skips the upload only, the load always runs (§3) |
| catalog fan-out | not considered | `coverage`, the raw cap and `metadata` with `parameters` reason at study level; `measurements`, `relationships` and the empty-state suggestion filter the fact rows themselves |
| pairs sample | `id % step` | `row_number() % step`, `sampled` true only when sampling happened (§7) |
| dictionary | #107's CSV | provisional CSVs in `api/data`, synced at boot and seed |
| frequencies routes | deleted | deleted; the five `PlotsDrawer` charts became one `MetadataTreemapChart` over `/stats/metadata` |
