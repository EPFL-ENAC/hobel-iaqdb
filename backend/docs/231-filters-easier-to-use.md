---
status: accepted
issue: 231
last_updated: 2026-11-26
summary: Split the Explore filter dialog into seven sections and add space and instrument filters.
---

# 231: Make the filters easier to use

This plan covers #231, the feedback of the survey on the Explore filters.
It extends the filter part of
[129-explore-charts-api.md](129-explore-charts-api.md).

## Problem

The filter dialog had five sections. "What & when" held the pollutants and
the measurement years together. The two pills of the filter bar, "every
parameter" and "any year", therefore opened the same page. The survey read
this as one filter shown twice (R8). The other remarks were these:

1. The pollutant list has no search and only one order, "most common" (R1).
2. "Buildings" holds the study, which is not a property of a building.
   "Spaces" holds only the ventilation. Space type, outdoor and HVAC air,
   and filtration have no filter (R2, R4).
3. There is no filter on how a value was measured: the grade of the
   instrument, where it sampled, and the time resolution (R2).

## Decisions

1. The dialog has seven sections: Pollutants, Measurement years, Where,
   Buildings, Spaces, People & surroundings, and Measurement. Each pill of
   the filter bar opens its own section. The Pollutants section says that
   no pick means every parameter. The Measurement years section says that
   the full range means every date. The two filters are independent: one
   says what was measured, the other says when.
2. The facet list takes a `sortable` option. With it, the reader orders
   the values by count ("Most common") or by name ("A to Z"). The search
   matches the label. With the `searchKeys` option, it also matches the
   key, so "co2" finds "CO₂". Only the pollutant list sets it, because the
   country keys are ISO codes and "de" then finds Germany.
3. Buildings holds the building type, the construction year and the
   mechanical ventilation, which is recorded per building.
4. Spaces holds the space type, the space use (the `occupancy` column),
   the ventilation type and the air filtration. Outdoor and HVAC supply
   air are values of the space type, so they need no filter of their own.
   The space type list is searchable because the data holds more than 25
   values.
5. Measurement holds the study, the instrument grade
   (`equipment_grade_rating`) and the sampling location (`placement`).
   The sampling location is free text with about 250 values, so its list
   is searchable. A note under the instrument grade says what an
   instrument filter counts (decision 8).
6. The explore filter dialect gains `$instrument`, next to `$building` and
   `$space`. Three dimensions join the registry: `air_filtration`,
   `instrument_grade` and `placement`.
7. Each reading of the fact tables carries its `instrument_id`, so the
   measurement queries filter and group by instrument exactly. A space
   mean (`grain=space`) pools the instruments of a space. It applies an
   instrument filter to the readings before the mean, but it cannot group
   by instrument and returns 422 for that.
8. Each reading carries its instrument, but the catalog links an
   instrument to its study only. The metadata and coverage queries
   therefore join the instruments through `instrument_links`. This
   subquery holds the distinct study, dataset, building, space, instrument
   and parameter of `measurement_day`. If a study, dataset, building or
   space holds no readings of an instrument of a grade, it does not count
   for that grade. If such an instrument logged a dataset and parameter
   pair, coverage keeps the pair and sums all its readings, from every
   instrument. If an instrument filter is set, the records totals of the
   filter bar and the hero count the measured days, so they stay exact.
9. The new criteria go to the explore routes only. The data hub drawer has
   no control to show or clear the space type, the space use, the air
   filtration or the instrument criteria. If its lists followed them, the
   reader does not see why rows are missing. The data hub keeps the
   filters it had before: the ventilation type is the only space
   criterion of the catalog routes.

## Out of scope

Time resolution is not a filter. No field of the study, the dataset, the
instrument or the dataset parameter summary holds a logging interval. To
add the filter, a data upload must first derive and store an interval for
each dataset and parameter. The data that is already loaded then needs a
backfill. The reason is in the comment on the issue:
<https://github.com/EPFL-ENAC/hobel-iaqdb/issues/231#issuecomment-7189018012>.

## Tests

1. `tests/test_stats_metadata.py::test_space_and_instrument_dimensions`
   groups spaces by air filtration and studies by instrument grade and
   sampling location. It filters datasets, buildings and spaces by
   instrument grade and keeps only those that the instrument measured.
2. `tests/test_stats_measurements.py::test_instrument_filter_reaches_each_reading`
   counts raw readings per instrument grade. It filters them at raw and
   day grain and in coverage. It also checks the 422 and the filter at
   `grain=space`.
3. The frontend has no test runner. `npm run typecheck` and `npm run lint`
   cover it.
