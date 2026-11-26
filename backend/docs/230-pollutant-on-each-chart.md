---
status: accepted
issue: 230
last_updated: 2026-11-26
summary: Every Explore chart that depends on the pollutant selection names its pollutants in the eyebrow. A chart that shows one pollutant names that pollutant and keeps its pollutant menu.
---

# 230: Name the pollutant on each chart

From the IAQ Database feedback survey of November 2026, raised by one participant.

## Problem

After a selection of formaldehyde and CO₂, the participant did not know which pollutant each chart showed.

Two kinds of charts caused this:

- Charts that show one pollutant. "Distribution by group" and "Monthly pattern" did not name their pollutant. If there is a choice, they show a pollutant menu. If only one pollutant was left, nothing named it. For example, a pollutant with no reference is not offered.
- Charts that count the selected pollutants together. Six of them did not say which pollutants they counted: the four "Datasets by …" charts, "Measurement period" and "Metadata availability".

## Decision

The eyebrow is the small line above the chart title. It says what the chart counts. It now also names the pollutants, after a middle dot:

| Chart | Eyebrow with CO₂ and formaldehyde selected |
| --- | --- |
| Distribution by group | Distribution by group · Carbon dioxide |
| Monthly pattern | Monthly pattern · Carbon dioxide |
| Datasets by country | Datasets by country · Carbon dioxide, Formaldehyde |
| Measurement period | Measurement period · Carbon dioxide, Formaldehyde |

A chart of one pollutant names the pollutant it shows. A chart of the selection names up to two pollutants. With three or more, it names the first and the count of the others, for example "Carbon dioxide +2", as the filter bar does. With no pollutant selected, the charts count every pollutant and the eyebrow names none.

`useChartFormat().withPollutants(eyebrow, slugs)` builds the text. The names are the schema labels, the same as in the "Relationship · Carbon dioxide × ventilation" eyebrows. The "Show all" dialogs use the same eyebrow as their chart.

## Charts left as they were

- "Relationship · … × ventilation", "× climate" and "× building", and "Explore pollutant patterns", already named their pollutant in the eyebrow.
- "Records by pollutant" has one row per pollutant and highlights the selected ones.
- "Records by calendar month" names the selected pollutants in its legend.
- The correlation matrix and the custom pair label each pollutant on the chart.

If more than one pollutant is offered, the four charts that show one pollutant already had a pollutant menu. This change keeps the menus as they are.

## Tests

The frontend has no test runner. `vue-tsc` and ESLint pass on the changed files.
