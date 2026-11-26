---
status: accepted
issue: 230
last_updated: 2026-11-26
summary: Each Explore chart has a download button at the end of its eyebrow line, or under its dropdown menus. It saves the chart as a PNG or SVG file. The footer of the file gives the filters, the units, the reference, the versions, the date and how to cite. The image is drawn again as SVG from the data of the card, with no new package.
---

# 230: Download a chart as an image

From the IAQ Database feedback survey of November 2026, raised by two participants.

## Problem

People put Explore charts in reports and slides. Today they take a screenshot. A screenshot does not say which filters were on, which units the values use, or which version of the database the chart comes from. It also does not say how to cite the database.

## Decision

Each chart card has a small download button, with an outlined icon, at the right end of its eyebrow line. The eyebrow line is the first line of the card, for example "Relationship · Carbon dioxide × ventilation". If a card has dropdown menus at the right of its title, the button is under these menus, at the right end. The button opens a menu with two items: PNG image and SVG image.

The file is a new drawing, not a copy of the screen. The image is 1000 px wide. From top to bottom, it has these parts:

1. The eyebrow, the title and the reading note of the card.
2. The chart.
3. The legend of the chart. A chart without a legend skips this part.
4. A footer.

The footer has one line for each of these items:

1. The filters, or "none".
2. The units of the pollutants in the chart.
3. The reference, with its value and its source.
4. Facts that the card shows beside the chart, for example r and the number of paired hours.
5. The release of the website, the data version, the lab, the page address and the download date.
6. How to cite.

The release comes from `package.json`. The build gives it to the app as `APP_VERSION`. The data version is the version of the explore schema.

### How the chart is drawn

Most charts on these pages are HTML, not ECharts. Each HTML chart part draws itself again as SVG from the same rows that the card shows. `RankedTable`, `RangeList` and `DistributionTable` register a drawing with the card that holds them. `ChartCard` collects these drawings in the order they set up. The copies in the "Show all" dialog do not register, so the image shows what the card shows.

The drawing functions are in `figureDrawings.ts`. The page layout, the PNG step and the file name are in `figureImage.ts`. The ranked bars always use the inline layout in the image, because the image has the room.

The ECharts charts use the SVG export of ECharts itself, at the image width and with no animation. The correlation matrix is HTML in its figure, so the figure gives its own drawing to the card.

The SVG file is a real vector file: text stays text and shapes stay shapes. The PNG is the same SVG, drawn on a canvas at two pixels for each SVG pixel.

### Why no package

A screenshot package copies the screen at the size of the card. It does not give a vector file, and its text depends on the fonts of the browser. A drawing from the data gives the same layout on every screen, and it adds no dependency.

## Open point

The citation line names an overview paper that is in preparation. When the paper is out, replace the line with the full reference.
