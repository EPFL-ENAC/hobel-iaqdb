---
status: accepted
issue: 230
last_updated: 2026-11-26
summary: Every Explore chart has a note under its title that says what one point, bar, row or cell is. Each scale has a title with its unit. The charts that compare groups say that a gap between groups has more than one cause.
---

# 230: Axis titles, units and "one point is" on each chart

From the IAQ Database feedback survey of November 2026, raised by two participants.

## Problem

One participant asked for axis titles, units and a short note on what one point or bar is, on every chart. People share these charts as screenshots, outside the website. A screenshot does not keep a tooltip.

Another participant saw that dwellings look warmer than schools. Without context, a reader takes this gap as an effect of the building use. But the groups also differ in season, occupancy and study.

## Decision

The reading note is a short grey text under the chart title. It says what one mark of the chart is. A screenshot that keeps the title also keeps the note. `ChartCard` and `FigureDialog` take it as the `note` prop, so the "Show all" dialog shows the same note.

| Chart | One mark is | Scale titles |
| --- | --- | --- |
| Datasets by … (four charts) | One bar: the datasets of one country, building type, climate zone or ventilation status | Header row |
| Records by pollutant | One bar: the records of one pollutant. A record is one reading of one instrument. | Header row |
| Measurement period | The running total of datasets, by the year of their first measurement | Year, Datasets so far |
| Records by calendar month | One bar: the records of one calendar month, all years together | Month, Records |
| Metadata availability | One bar: the share of studies, buildings or spaces with the field filled in | Header row |
| Distribution by group | One row: the spread of the means of one group, at the averaging period of the reference | "Daily mean (ppm)", from the reference |
| Monthly pattern | One point: the median of the daily means of one month, or of one day after a click | "Daily mean (ppm)" |
| Relationship × ventilation, climate, building | One row: the median and middle half of the means of one group, or of one dataset | "Daily mean (ppm)", from the reference |
| Explore pollutant patterns | One point: one space, its mean over the period | The metric with its unit, the pollutant with its unit |
| Correlation matrix | One cell: the correlation of two pollutants over their shared hours. The note also gives the colors. | Row and column labels |
| Custom pair | One dot: one hour in one space | Already there |

A dataset can count in more than one bar of a "Datasets by …" chart, for example in two countries. The note says so, except at the study level: a dataset belongs to one study only.

The group figures had no scale. `RangeList` now writes the ticks and the scale title under the last range. `DistributionTable` writes the scale title under its ticks. The title says the averaging period and the unit, for example "Hourly mean (ppm)".

The "Distribution by group" footer described the reference line, the database median line and the box. The box moved to the note, because the footer cut the line short.

The group figures and "Distribution by group" add this caveat to the note: "A gap between groups is not due to the building type alone: the groups also differ in other ways, such as season, occupancy and the study that measured them." The note names the level shown. At the dataset level, the group figures leave the caveat out.

Two metric labels did not have a unit. "Occupancy density" is now "Occupancy density (persons/m²)", and "Airtightness" is now "Airtightness (ACH50)". The catalog uses the same units.

## ECharts axis titles

`charts.ts` has two helpers. `axisTitle('x' | 'y', name)` gives an axis title in the style of the custom pair chart. `plotGrid(margins)` keeps the axis labels and the axis titles inside the margins. `containLabel: true` keeps the labels inside but not the titles, so the charts with a title use `plotGrid` in its place.

## Out of scope

The other tasks of #230 are separate: the method note on time resolution and the chart download as an image.
