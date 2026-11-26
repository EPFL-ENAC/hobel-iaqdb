/**
 * The HTML charts of the explore page drawn again as SVG, for the image of
 * their card: from the rows the card shows, at the image's width, in the
 * sizes and colours of their stylesheets, without their hover states.
 */
import {
  ACCENT,
  ACCENT_TINT,
  GAP,
  GREY_3,
  GREY_4,
  GREY_7,
  GREY_8,
  INK,
  MUTED_FILL,
  TRACK,
  baseline,
  escape,
  fit,
  line,
  rect,
  round,
  text,
  textWidth,
  type Drawing,
} from '@/components/explore/figureImage';

const BODY = 15;
const SMALL = 12;
const HEAD = 11;

/** a line of RankedTable */
export interface RankedLine {
  label: string;
  value: string;
  cells: string[];
  /** the bar's length, 0..1 of the longest */
  share: number;
  /** a colour, `url(#hatch)` or `url(#hatch-muted)`, or `none` for no bar */
  fill: string;
  summary: boolean;
}

export interface RankedDrawing {
  labelHeader: string;
  barHeader: string;
  valueHeader: string;
  columnHeaders: string[];
  /** the share of the width the labels get, 0..1 */
  labelShare: number;
  lines: RankedLine[];
}

/** the inline layout of RankedTable: label, bar and values side by side */
export function drawRanked(table: RankedDrawing, width: number): Drawing {
  const GAP_X = 20;
  const ROW = 34;
  const headers = [table.valueHeader, ...table.columnHeaders];
  // each value column is as wide as its widest text, as `auto` in the grid
  const valueWidths = headers.map((header, i) =>
    Math.max(
      textWidth(header.toUpperCase(), HEAD) + header.length * 0.44,
      ...table.lines.map((entry) => textWidth((i ? entry.cells[i - 1] : entry.value) ?? '', BODY, 600)),
    ),
  );
  const labelWidth = width * table.labelShare;
  const trackX = labelWidth + GAP_X;
  const trackWidth = width - trackX - valueWidths.reduce((sum, w) => sum + w + GAP_X, 0);
  // the right edge of each value column
  const valueRights = valueWidths.map(
    (_, i) => trackX + trackWidth + valueWidths.slice(0, i + 1).reduce((sum, w) => sum + w + GAP_X, 0),
  );
  const head = { size: HEAD, color: GREY_7, spacing: 0.44 };

  const parts: string[] = [];
  let y = 0;
  const headBase = baseline(y + 6, 16, HEAD);
  if (table.labelHeader)
    parts.push(
      text(labelWidth, headBase, fit(table.labelHeader.toUpperCase(), labelWidth, HEAD), { ...head, anchor: 'end' }),
    );
  if (table.barHeader) parts.push(text(trackX, headBase, table.barHeader.toUpperCase(), head));
  headers.forEach((header, i) => {
    if (header) parts.push(text(valueRights[i] ?? 0, headBase, header.toUpperCase(), { ...head, anchor: 'end' }));
  });
  y += 6 + 16 + 8;

  for (const entry of table.lines) {
    const base = baseline(y, ROW, BODY);
    parts.push(text(labelWidth, base, fit(entry.label, labelWidth, BODY), { size: BODY, anchor: 'end' }));
    if (entry.fill !== 'none')
      parts.push(rect(trackX, y + (ROW - 18) / 2, Math.max(2, entry.share * trackWidth), 18, entry.fill));
    [entry.value, ...entry.cells].forEach((value, i) => {
      parts.push(
        text(valueRights[i] ?? 0, base, value, { size: BODY, anchor: 'end', weight: entry.summary && !i ? 600 : 400 }),
      );
    });
    y += ROW;
    if (entry.summary) {
      y += 6;
      parts.push(line(0, y, width, y, GREY_4));
      y += 8;
    }
  }
  return { svg: parts.join(''), height: y };
}

/** a row of RangeList */
export interface RangeLine {
  label: string;
  sublabel: string;
  value: string;
  /** places on the scale, 0..1 */
  low: number;
  mid: number;
  high: number;
}

export interface RangeDrawing {
  rows: RangeLine[];
  /** the reference's place, 0..1, or null */
  reference: number | null;
  ticks: { at: number; text: string }[];
  axisTitle: string;
}

/** RangeList: a line with the label and value, under it the track with the range and its dot */
export function drawRanges(list: RangeDrawing, width: number): Drawing {
  const parts: string[] = [];
  let y = 0;
  for (const row of list.rows) {
    const base = baseline(y, 21, BODY);
    const valueWidth = textWidth(row.value, BODY);
    parts.push(text(width, base, row.value, { size: BODY, anchor: 'end' }));
    // the sublabel gives way first, then the label
    const room = width - valueWidth - 12;
    const label = fit(row.label, room, BODY);
    parts.push(text(0, base, label, { size: BODY }));
    const after = textWidth(label, BODY) + 6;
    if (row.sublabel && room - after > 24)
      parts.push(text(after, base, fit(`· ${row.sublabel}`, room - after, SMALL), { size: SMALL, color: GREY_7 }));
    y += 21 + 10;

    parts.push(rect(0, y, width, 6, TRACK));
    parts.push(rect(row.low * width, y, (row.high - row.low) * width, 6, ACCENT, 'fill-opacity="0.7"'));
    parts.push(`<circle cx="${round(row.mid * width)}" cy="${round(y + 3)}" r="7" fill="${ACCENT}"/>`);
    if (list.reference !== null)
      parts.push(line(list.reference * width, y - 7, list.reference * width, y + 13, GAP, 'stroke-width="2"'));
    y += 6 + 20;
  }
  if (list.rows.length && (list.ticks.length || list.axisTitle)) {
    y -= 8;
    list.ticks.forEach((tick, i) => {
      const anchor = i === 0 ? 'start' : i === list.ticks.length - 1 ? 'end' : 'middle';
      parts.push(text(tick.at * width, baseline(y, 16, SMALL), tick.text, { size: SMALL, color: GREY_7, anchor }));
    });
    y += 16;
    if (list.axisTitle) {
      parts.push(
        text(width, baseline(y + 4, 16, SMALL), list.axisTitle, { size: SMALL, color: GREY_7, anchor: 'end' }),
      );
      y += 20;
    }
  } else y -= 20;
  return { svg: parts.join(''), height: Math.max(0, y) };
}

/** a row of DistributionTable, its percentiles placed on the scale, 0..1 */
export interface BoxLine {
  label: string;
  sublabel: string;
  p05: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
  /** 0..1, or null when unknown */
  share: number | null;
  shareText: string;
}

/** a line across every row: the reference, solid, or the database median, dashed */
export interface BoxMark {
  kind: 'reference' | 'median';
  at: number;
  text: string;
  side: 'left' | 'right';
}

export interface BoxDrawing {
  rows: BoxLine[];
  ticks: { at: number; text: string }[];
  marks: BoxMark[];
  shareHeader: string;
  axisTitle: string;
}

/** DistributionTable: the label, the box plot on the shared scale, then the share */
export function drawBoxes(table: BoxDrawing, width: number): Drawing {
  const ROW = 64;
  const GAP_X = 32;
  const labelWidth = width * 0.16;
  const shareWidth = width * 0.24;
  const plotX = labelWidth + GAP_X;
  const plotWidth = width - labelWidth - shareWidth - 2 * GAP_X;
  const shareX = plotX + plotWidth + GAP_X;
  const percentWidth = BODY * 3.5;
  const trackWidth = shareWidth - 12 - percentWidth;
  const x = (at: number) => plotX + at * plotWidth;

  const parts: string[] = [];
  if (table.shareHeader)
    parts.push(text(shareX, baseline(0, 13, HEAD), table.shareHeader, { size: HEAD, color: GREY_7 }));
  const top = 13 + 12;
  const bottom = top + table.rows.length * ROW;

  if (table.rows.length) {
    for (const tick of table.ticks) parts.push(line(x(tick.at), top, x(tick.at), bottom, GREY_3));
    table.rows.forEach((row, i) => {
      const middle = top + i * ROW + ROW / 2;
      const name = fit(row.label, labelWidth, BODY);
      if (row.sublabel) {
        parts.push(text(0, middle - 3, name, { size: BODY }));
        parts.push(text(0, middle + 14, fit(row.sublabel, labelWidth, 13), { size: 13, color: GREY_7 }));
      } else parts.push(text(0, baseline(middle - 11, 22, BODY), name, { size: BODY }));

      parts.push(line(x(row.p05), middle, x(row.p95), middle, ACCENT));
      parts.push(rect(x(row.p25), middle - 13, x(row.p75) - x(row.p25), 26, ACCENT_TINT, `stroke="${ACCENT}"`));
      parts.push(line(x(row.p50), middle - 13, x(row.p50), middle + 13, INK, 'stroke-width="2"'));

      parts.push(rect(shareX, middle - 9, trackWidth, 18, MUTED_FILL));
      if (row.share !== null) parts.push(rect(shareX, middle - 9, row.share * trackWidth, 18, ACCENT));
      parts.push(text(shareX + trackWidth + 12, baseline(middle - 11, 22, BODY), row.shareText, { size: BODY }));
    });

    // over the boxes, each with its value read from bottom to top beside it
    for (const mark of table.marks) {
      const at = x(mark.at);
      const color = mark.kind === 'reference' ? GAP : GREY_7;
      const stroke = mark.kind === 'reference' ? 'stroke-width="2"' : 'stroke-dasharray="3 3"';
      parts.push(line(at, top, at, bottom, color, stroke));
      const length = textWidth(mark.text, HEAD) + 4;
      const left = mark.side === 'left' ? at - 3 - 13 : at + 3;
      parts.push(rect(left, top + 2, 13, length, 'white', 'fill-opacity="0.85"'));
      const ink = mark.kind === 'reference' ? GAP : GREY_8;
      parts.push(
        `<text transform="translate(${round(left + 10)} ${round(top + 4)}) rotate(-90)" font-size="${HEAD}" fill="${ink}" text-anchor="end">${escape(mark.text)}</text>`,
      );
    }

    for (const tick of table.ticks)
      parts.push(text(x(tick.at), bottom + 12 + 11, tick.text, { size: SMALL, color: GREY_7, anchor: 'middle' }));
  }
  let height = bottom + 32;
  if (table.axisTitle && table.rows.length) {
    parts.push(text(plotX + plotWidth, height + 12, table.axisTitle, { size: SMALL, color: GREY_7, anchor: 'end' }));
    height += 18;
  }
  return { svg: parts.join(''), height };
}

/** a cell of the correlation matrix */
export interface MatrixCell {
  text: string;
  fill: string;
  /** 0..1: the stronger the correlation, the deeper */
  opacity: number;
  ink: string;
  strongest: boolean;
}

export interface MatrixDrawing {
  labels: string[];
  /** a row per label, a cell per label */
  cells: MatrixCell[][];
  height: number;
}

/** the correlation matrix: a label left of each row and under each column */
export function drawMatrix(matrix: MatrixDrawing, width: number): Drawing {
  const n = matrix.labels.length;
  const GAP_X = 8;
  const SIZE = 13;
  const labelWidth = Math.max(0, ...matrix.labels.map((label) => textWidth(label, SIZE))) + 4;
  const cellWidth = (width - labelWidth - n * GAP_X) / n;
  const cellHeight = (matrix.height - 24 - n * GAP_X) / n;
  const parts: string[] = [];
  matrix.labels.forEach((label, j) => {
    const top = j * (cellHeight + GAP_X);
    parts.push(text(labelWidth, baseline(top, cellHeight, SIZE), label, { size: SIZE, anchor: 'end' }));
    matrix.cells[j]?.forEach((cell, i) => {
      const left = labelWidth + GAP_X + i * (cellWidth + GAP_X);
      const extra = [
        cell.opacity < 1 ? `fill-opacity="${Math.round(cell.opacity * 100) / 100}"` : '',
        cell.strongest ? `stroke="${INK}" stroke-width="2"` : '',
      ];
      parts.push(rect(left, top, cellWidth, cellHeight, cell.fill, extra.filter(Boolean).join(' ')));
      parts.push(
        text(left + cellWidth / 2, baseline(top, cellHeight, SIZE), cell.text, {
          size: SIZE,
          color: cell.ink,
          anchor: 'middle',
        }),
      );
    });
  });
  const labelsTop = n * (cellHeight + GAP_X);
  matrix.labels.forEach((label, i) => {
    const center = labelWidth + GAP_X + i * (cellWidth + GAP_X) + cellWidth / 2;
    parts.push(
      text(center, baseline(labelsTop, 24, SIZE), fit(label, cellWidth, SIZE), { size: SIZE, anchor: 'middle' }),
    );
  });
  return { svg: parts.join(''), height: labelsTop + 24 };
}
