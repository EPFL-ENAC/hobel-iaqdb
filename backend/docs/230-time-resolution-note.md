---
status: accepted
issue: 230
last_updated: 2026-11-26
summary: A short method note in the Explore help drawer tells how Explore makes hourly means, daily means and the mean of a space. It also tells which mean each chart uses. The footer of each chart that shows values or record counts links to it. The note says that Explore leaves out summary statistics. Samples over a period, for example from passive samplers, count as one reading at the start of their period. No backend change.
---

# 230: A method note on time resolution

From the IAQ Database feedback survey of November 2026, raised by two participants.

## Problem

One participant asked how the app combines values measured every minute, every 10 minutes or over several days. Another participant needed time to see that the relationship charts pool the hourly pairs of all the datasets. The reading note under each chart title says which mean the chart uses, but no page tells how these means are made.

## Decision

The note is `frontend/public/time-resolution.md`. It opens in the help drawer, the same drawer as the other help notes. It has these sections:

1. Hourly means, per dataset, space, instrument and pollutant, in the local clock time of the study.
2. Daily means and the mean of a space, both as the mean of all their readings.
3. Which mean a chart uses: the averaging time of the reference, or daily means without a reference. The monthly pattern always shows daily means. The relationship charts pair hourly means of one dataset, space and hour, and pool all the datasets in scope.
4. How much each record counts: each hourly or daily mean counts once in the medians, the percentiles and the shares above a reference. The record counts count every reading.
5. What is left out, and what is not.

Up to now, the help drawer opened only on the data hub. Explore gets its own drawer in `MainLayout.vue`. It opens over the page, with a backdrop, and a click outside it closes it.

`TimeNoteLink.vue` is the link: a question mark icon and the words "Hourly & daily means". Its tooltip says "How readings at different time steps are combined". If a card sets `time-note`, `ChartCard` shows the link at the right end of the footer. The items of the card's own footer, for example "Show all" or a hint, stay at their place on the left of the link. "Records by pollutant" draws its footer in `RankedBars`, so it puts the link in the hint slot.

These cards carry the link, because they show values or record counts made from the readings:

1. The relationship of a pollutant with a building aspect, the distribution by group and the monthly pattern.
2. Records by calendar month and records by pollutant.
3. The relationship with space metrics, the custom pair and the correlation matrix.

Metadata availability, the measurement period and the dataset counts by country, building type, climate zone and ventilation do not carry the link. They count datasets, spaces and periods, and they do not combine readings.

## What is left out

The note was to say which measurements are left out, for example passive samplers. The code does not leave them out. A row of type `time_integrated` loads into `measurement` with its time set to the start of its period. The continuous aggregates `measurement_hour` and `measurement_day` thus count it as one reading in its first hour and on its first day. Only rows of type `statistical` are left out. They go to `measurement_statistic` (#174), and Explore does not show them yet.

The note thus says what the code does. It says that the charts treat a 7-day sample like a 1-hour reading. This matters most for pollutants such as formaldehyde, nitrogen dioxide and benzene. In the local database, 13 datasets have samples over more than one day, for example 8 of the 17 formaldehyde datasets.

## Open point

Issue #236 is about the handling of samples over a period. When #236 changes how Explore counts them, update the last section of the note.
