---
status: accepted
issue: 229
last_updated: 2026-11-24
summary: The correlation matrix opens on CO2, PM2.5, air temperature, relative humidity and NO2. It adds the pollutants selected in the filters. A dialog picks its pollutants. The pair chart opens on CO2 against PM2.5.
---

# Default parameters and a parameter picker

Third task of issue #229, from the IAQ Database feedback survey of November 2026. Six participants raised it.

## Problem

The correlation matrix opened on CO2, relative humidity, NO2, PM2.5 and PM10. The pair chart opened on PM2.5 against PM10. Neither set came from what users asked for. When two or more pollutants selected in the filters had data, they replaced the whole default set. The matrix menu was a small multiple select, and respondent R3 asked for a clearer way to pick the matrix parameters.

The survey gave no majority on the method or on the size of the matrix. The matrix keeps 5 parameters and the Spearman method.

## Decision

### Correlation matrix

The matrix opens on the five parameters that most respondents named, in this order: CO2, PM2.5, air temperature, relative humidity and NO2 (`DEFAULT_SET` in `CorrelationFigure.vue`).

The matrix adds each pollutant selected in the filters that the set does not hold (R5). The matrix order is the set, then the pollutants of the filters. Only pollutants with records under the filters go in. The endpoint caps a matrix at 10 parameters. Past the cap, the pollutants of the filters stay and the last pollutants of the set go. With fewer than two pollutants left, the pollutants with records fill the matrix up to five.

A button with the number of pollutants opens a dialog (`MatrixPicker.vue`, R3). The dialog lists the pollutants with records, with a bar of their records under the filters, and a search field. The pollutants of the matrix come first, then the others by records. When the user checks a row, the row does not move. The pollutants of the filters are checked and disabled, and a line above the list names them. "Default" goes back to the default set, plus the pollutants of the filters. "Apply" needs 2 pollutants at least. At 10 pollutants, the unchecked rows are disabled.

The pick of the dialog replaces the default set until the page reloads. A pollutant of the filters stays out of the pick, unless the pick held it before. So, when the user removes a pollutant from the filters, it leaves the matrix, unless the user picked it.

`FacetList.vue` takes a `format` for its counts, and reads the width of its count column from `--facet-count-width`. A record count such as "11M" does not fit in the 32 px of the filter dialog.

### Pair chart

The pair chart opens on CO2 on the X axis and PM2.5 on the Y axis, as 3 of 6 answers asked. If a filter leaves no common hours for this pair, the chart falls back as before: the first X with partners, then the first Y among them.

## Cost

No new request. The dialog reads the coverage request that the matrix already sends. The default set holds 5 parameters, as before, so the matrix still has 10 cells.

## Tests

The frontend has no test runner. `vue-tsc` and `eslint` check the frontend changes. The backend does not change.
