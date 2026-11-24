---
status: accepted
issue: 229
last_updated: 2026-11-24
summary: The pair chart and "Explore pollutant patterns" split a relationship by building type or ventilation, one small chart per group. `pairs` takes the method and samples its dots per group.
---

# Split relationships by building type and ventilation

Second task of issue #229, from the IAQ Database feedback survey of November 2026. This plan builds on the first task (`229-studies-behind-each-r.md`).

## Problem

Three survey participants want to see a relationship inside one kind of building or ventilation. For example, respondent R5 wants CO2 against occupancy density for naturally and mechanically ventilated classrooms side by side. Respondent R4 wants the effect of ventilation or air purification on occupancy and IAQ.

Filtration is not part of this task. It waits for the filtration and air cleaner fields of #235.

## What the API already gives

`agg=pairs` already takes `by`, for two parameters and for a catalog metric `x`. Each bucket of a dimension key has its own `n`, `fit`, `points`, `n_spaces`, `n_studies` and `within`. Two gaps stop the charts from using it:

1. The pair chart gets its Spearman r from `agg=matrix` with two parameters, and the matrix takes no `by`.
2. The dots of `pairs` are one sample over all the buckets: every `ceil(total / 2000)`-th row. A small group gets few dots or none. On the dev database, CO2 against PM2.5 by building type gives 52 pairs for "hospital" and no dot.

## Decision

### Backend

`pairs` takes `method`, `pearson` (the default) or `spearman`, for two parameters and for a catalog metric:

| Field | Content |
| --- | --- |
| `fit.r` | The r of the bucket by the method. For Spearman, the ranks are inside the bucket. |
| `within.studies[].r` | The r of the study inside the bucket, by the same method. For Spearman, the ranks are inside the study and the bucket. |
| `fit.slope`, `fit.intercept`, `fit.r2` | Always the least-squares fit of y on x, over the values. The trend line does not change with the method. |

The fit statement reads a subquery of the paired rows: the dimension keys, x, y, the space and the study. For Spearman, the subquery also ranks x and y inside the bucket, and inside the bucket and the study. These are the same average ranks as the Spearman matrix, so ties get their average rank. For Pearson, PostgreSQL merges the subquery into the outer statement, so the plan does not change.

Each bucket gets its own sample of dots. The quota of a bucket is `ceil(2000 / number of buckets)`. A bucket keeps every `ceil(n / quota)`-th row, in the order of dataset, space and time. Without `by`, there is one bucket, and the sample is the same as before. `sampled` is true for a bucket that has more rows than its quota.

`matrix`, `partners` and `partnered` do not change.

### Frontend

Both charts get a "Split by" menu. It offers "None", building type, mechanical ventilation (yes or no, from the building) and ventilation type (from the space). `SPLIT_DIMENSIONS` in `charts.ts` holds this list. The filtration task of #235 adds its dimension there.

With a split, the chart draws one small chart per group, in the order of the buckets: by `n` descending, then by key, and no key last. A group without a key is "Not recorded". All small charts have the same axis ranges, so that the reader can compare them. Each small chart gives its group, and its r or "Too little data". It gives its studies, as a link to the study list, and its spaces. One line gives the r within each study. The pair chart also gives the paired hours of each group.

Without a split, the charts do not change.

The pair chart now gets every r from `pairs` with its method, without a split and with one. It no longer sends a matrix of two for Spearman. This is one request instead of two.

"Explore pollutant patterns" keeps its probes, one `pairs` request per metric without a split. They decide which metrics the menu offers. With a split, one more `pairs` request with `by` gets the groups of the chosen metric. The small charts draw the reference line of the pollutant without its label, because they have no room for it. The footer gives the reference instead.

While a new split loads, each chart keeps the groups of the last result on show. The chart reads the split from `meta.dimensions` of the result, not from the menu.

`SplitPanels.vue` draws the small charts for both charts. `scatter.ts` builds the scatter option of both charts and of each small chart. This keeps `PairFigure.vue` under the limit of 500 lines.

## Cost

Cost on the dev database on 2026-11-23, local, at the hour grain. The "before" numbers come from the two requests of a Spearman pair chart, which load in parallel. The "after" numbers come from one `pairs` request, through the service, warm.

| Query | Before | After |
| --- | --- | --- |
| Spearman CO2 × air temperature, 1.7 M pairs | 3.3 s (`pairs`) and 6.5 s (matrix of two) | 8.1 s |
| Spearman PM2.5 × PM10, 0.4 M pairs | 1.0 s (`pairs`) and 1.3 s (matrix of two) | 1.7 s |
| Pearson CO2 × air temperature | 3.3 s | 3.3 s |
| Pearson CO2 × PM2.5 by building type, 9 groups | 1.8 s, no dot for "hospital" | 1.9 s, 52 dots for "hospital" |
| Spearman CO2 × PM2.5 by building type | not possible | 3.0 s |
| Spearman CO2 × air temperature by ventilation | not possible | 8.1 s |
| Spearman occupancy density × CO2 by ventilation | not possible | 0.7 s |

The Spearman chart of CO2 against temperature waits 1.5 s longer than before, because one request now does the work of two. The database does less work in total: 8.1 s against 9.8 s. The Pearson chart, the default, does not change.

## Tests

`tests/test_stats_relationships.py` checks these points against plain Python:

- `pairs` with `method=spearman`, for two parameters and for a catalog metric. It checks the pooled r, the r of each study, and that the slope does not change with the method.
- `pairs` with `method=spearman` and `by`. The ranks are inside each bucket.
- The sample of dots per bucket, with a small `SAMPLE`. Each bucket gets dots up to its quota, and `sampled` is true only for a bucket above its quota.

The frontend has no test runner. `vue-tsc` and `eslint` check the frontend changes.
