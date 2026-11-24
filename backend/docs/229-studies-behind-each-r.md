---
status: accepted
issue: 229
last_updated: 2026-11-23
summary: Each relationship r gives its studies, spaces and points. It also lists its studies with the r inside each, and their median. Builds on #226.
---

# Studies behind each r, and r within each study

First task of issue #229, from the IAQ Database feedback survey of November 2026. This plan builds on #226 (`226-correlation-minimum-sample.md`), which added `n_spaces`, `enough` and the minimum sample size.

## Problem

A pooled r can come from differences between studies, not from a relationship inside any of them. On the dev database, CO2 against occupancy density gives r = 0.96 from 11 spaces that fall into two groups (survey respondent R2). The charts did not say how many studies were behind an r, so a reader did not see this. Respondent R5 wants to test a relationship inside one study.

## Decision

Two new fields on the relationship buckets of `agg=pairs` (parameter or catalog metric `x`) and `agg=matrix`:

| Field | Content |
| --- | --- |
| `n_studies` | The studies behind `n`. With `n_spaces` (#226) and `n`, the reader sees studies, spaces and points. |
| `within` | `{median, studies}`. `studies` has one entry per study behind `n`. `median` is the median of their r. If no study has an r, there is no `median`. |

Each entry of `within.studies` has these fields:

| Field | Content |
| --- | --- |
| `study` | The study identifier, the key of the `study` dimension. The study page opens with it. |
| `n`, `n_spaces` | The pairs and the spaces of the study alone. |
| `enough` | True if the study reaches the minimum sample size of #226 by itself. |
| `r` | The r of the study alone, by the method of the pooled r: Pearson or Spearman. |

A study gets an `r` only if `enough` is true. For two parameters, the minimum is `MIN_PAIRS` pairs over `MIN_SPACES` spaces. For a catalog metric, it is `MIN_SPACES` spaces. A study where one variable does not vary has no r, even with `enough`.

The studies with an r come first, by r ascending. The other studies follow, by `n` descending.

The pooled bucket keeps its #226 behavior. Below the minimum it has no `fit`, but it still gets `n_studies` and `within`.

The full list goes to the client, not only the median and a spread. With two studies the list is the spread. With 40, the chart draws one dot per study. The popup lists each study with its numbers. The client computes nothing from the list: the median comes from the backend, and the range is the first and last r of the sorted list.

The entries carry the identifier, not the name. The Explore page already loads the study names once, for the chart labels. On the dev database, the five-pollutant matrix answer is 21 KB.

`partners` and `partnered` do not change. They feed the menus, not an r.

## SQL

Each aggregation stays one statement. The fit query groups by `GROUPING SETS ((keys), (keys, study_id))`. The first set gives the pooled row, as before. The second gives one row per study, with its `study_id`. `grouping(study_id)` tells them apart. A second, small query reads the identifiers of these studies from the `study` table.

- `pairs` of two parameters: the self-join is the cost, so the second set is almost free.
- `pairs` with a catalog metric: the per-space subquery also returns `study_id`.
- `matrix`, Pearson: the pivot also groups by `study_id`. This does not change its rows, because a dataset belongs to one study.
- `matrix`, Spearman: each pair also ranks both columns inside each study (`partition by study_id`). These are two more sorts per pair.

`n_studies` is the number of study rows with pairs, not a `count(distinct study_id)`. A distinct count sorts every row again.

Cost on the dev database (87 studies, 8.9 M hourly rows), local, median of three runs, with the five default pollutants of the matrix:

| Query | Before | After |
| --- | --- | --- |
| `matrix`, Pearson | 3.0 s | 3.3 s |
| `matrix`, Spearman | 8.1 s | 13.3 s |
| `pairs` CO2 × air temperature | 3.0 s | 3.1 s |
| `pairs` PM2.5 × PM10 | 1.0 s | 0.9 s |
| `pairs` occupancy density × CO2 | 0.7 s | 0.7 s |

The Spearman matrix is the expensive one. For its largest pair, the pivot takes 1.4 s, the pooled ranks 0.55 s and the ranks inside the studies 0.55 s more. All sorts stay in memory at the 64 MB of `SORT_MEMORY`. The server cache keeps an answer for 10 minutes. If the matrix is too slow, a separate request for the within-study numbers can load after the pooled matrix. That is a contract change for later, not part of this task.

On the dev database, occupancy density against CO2 gives a pooled r of 0.96 from 11 spaces in 2 studies. The r inside these 2 studies is −0.32 and 0.30.

## Frontend

- The matrix shows the number of studies under each r. The tooltip gives r, studies, spaces and paired hours, then the median r within studies and its range. A click on a square opens the study list. Its "Plot this pair" button opens the pair chart, as the click did before.
- The pair chart lists studies and spaces with the pairs. The number of studies is a link to the study list. Under the method, a strip shows one dot per study on a scale from −1 to 1, and the median.
- "Explore pollutant patterns" says studies and spaces under the chart, then the median r within studies. "N studies" is a link to the study list.

`StudiesDialog.vue` is the study list for the three charts. Its title is the pair. Above the rows, it gives the r of all studies together and the median r within the studies. Each row gives the study name, with a link to the study page, its r, and its spaces and paired hours. A pooled r far from the r of each study comes from the differences between the studies. A study without an r says why: too little data, or a variable that does not vary.

`StudySpread.vue` draws the strip and one line of text for the pair chart. For Spearman, the strip and the list use the `within` of the matrix of two, which gives the Spearman r of the pair. `describeWithin` in `useChartFormat.ts` writes the line for the three charts. Below two studies there is no line, because the r of a single study is the pooled r.

If a bucket has no `n_studies`, the charts show no study count. They do not show zero.

## Tests

`tests/test_stats_relationships.py` uses a second study with its own spaces, so that the pooled r and the r inside each study differ. It checks `n_studies`, the order of `within.studies`, the r, `n` and `n_spaces` of each study, and `within.median` against plain Python. It does this for `pairs` of two parameters, `pairs` with a catalog metric, and both matrix methods. It also checks that a study below the minimum has `enough` false and no r, but counts in `n_studies`.
