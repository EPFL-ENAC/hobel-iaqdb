---
status: accepted
issue: 226
last_updated: 2026-11-23
summary: Below a minimum sample size, relationship queries return no r and no fit. Each bucket gets n_spaces and enough, so that the menus can hide the pair and the charts can say why. The construction year axis shows 1995, not 1,995.
---

# Correlation minimum sample size and construction year format

Issue #226, from the IAQ Database feedback survey of November 2026.

## Problem

Respondents got r = 0.00 and R² = 0.00 from one point or one space, for example benzene against occupant density. The backend returned a null r for these cases, and the "Explore pollutant patterns" chart showed a null r as 0.00. Even with many hourly pairs, a correlation from one or two spaces is noise.

The "Explore pollutant patterns" chart showed the construction year as "1,995". The axis used the ECharts default number format, and the tooltip used the format for measured values.

## Decision

The minimum lives in `api/services/explore/relationships.py`:

| Constant | Value | Applies to |
| --- | --- | --- |
| `MIN_SPACES` | 3 | every relationship |
| `MIN_PAIRS` | 30 | pairs of two parameters, matrix cells, partners |

A metric against a pollutant has one point per space, so only `MIN_SPACES` applies. The team can change the two values without other code changes.

Below the minimum, a bucket keeps `n`, its points and its new `n_spaces` count. It has `enough: false` and no `slope`, `intercept`, `r2` or `r`. The `pairs`, `matrix` and `partners` aggregations all return `n_spaces` and `enough`. The menus use them to hide a pair before the user can pick it.

## Frontend

- The pair chart hides X and Y options below the minimum. If X has no partner above the minimum, the chart says "Too little data for a correlation". It also lists the number of spaces.
- The "Explore pollutant patterns" chart hides metrics below the minimum, and pollutants with no metric above it. If the pollutant has pairs but no metric reaches the minimum, the chart says "Too little data for a correlation". It never shows a missing r as 0.00.
- The matrix leaves these cells blank. Their tooltip gives the reason, the spaces and the paired hours.
- `useChartFormat().formatYear` formats years without a thousands separator. The "Explore pollutant patterns" chart uses it on the x axis and in the tooltip for `building.construction_year`.

## Tests

`tests/test_stats_relationships.py` checks the cutoff on parameter pairs, metric pairs, both matrix methods and partners, with the real minimum. The earlier tests set the minimum to 1, because the fixture pairs only two spaces and those tests check the statistics.
