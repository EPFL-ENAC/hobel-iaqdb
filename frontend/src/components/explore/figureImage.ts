/**
 * A figure as an image file: the card's heading, the chart drawn again as
 * SVG at a set width, its legend, then a footer with the filters, the units,
 * the version and how to cite. The PNG is the same SVG, rasterized at twice
 * its size. The parts of a card that draw a chart register a drawing with
 * the card; ECharts charts draw themselves with ECharts' own SVG export.
 */
import type { InjectionKey } from 'vue';
import type { EChartsOption } from 'echarts';
import type { ExploreBenchmark } from '@/models';
import { init } from 'echarts/core';

/** a chart drawn at a width: its markup, from 0,0, and its height */
export interface Drawing {
  svg: string;
  height: number;
}

export type Draw = (width: number) => Drawing;

/** a colour of the chart and what it stands for */
export interface LegendItem {
  color: string;
  label: string;
  /** after the label, in grey, e.g. "80–100%" */
  detail?: string;
}

/** what a figure adds to its image, beyond the parts that register */
export interface FigureImage {
  /** the chart, when no part of the card draws it, e.g. an ECharts chart */
  draw?: Draw;
  legend?: LegendItem[];
  /** the pollutants the chart shows: the footer gives their units */
  pollutants?: string[];
  /** the reference the chart draws as a red line: the footer names it */
  reference?: ExploreBenchmark | null;
  /** more lines for the footer, e.g. the reference */
  notes?: string[];
}

/** what a card collects from the parts it holds; `add` returns the removal */
export interface ImageParts {
  add(draw: Draw): () => void;
}

/** a dialog provides null: the copies of a part in "Show all" draw nothing */
export const IMAGE_PARTS: InjectionKey<ImageParts | null> = Symbol('image-parts');

/** draws a part into the image of the card it sits in */
export function useImagePart(draw: Draw): void {
  const parts = inject(IMAGE_PARTS, null);
  if (!parts) return;
  onBeforeUnmount(parts.add(draw));
}

// the app's colours, as in quasar.variables.scss
export const INK = '#212121';
export const GREY_9 = '#424242';
export const GREY_8 = '#616161';
export const GREY_7 = '#757575';
export const GREY_4 = '#e0e0e0';
export const GREY_3 = '#eeeeee';
export const ACCENT = '#4aa39a';
export const ACCENT_TINT = '#d4ebe8';
export const MUTED_FILL = '#e3e3e3';
export const TRACK = '#f0f0f0';
export const GAP = '#e5392b';

const FONT = 'Helvetica, Arial, sans-serif';

let context: CanvasRenderingContext2D | null = null;

/** the width of a line of text, as the browser draws it */
export function textWidth(text: string, size: number, weight = 400): number {
  if (!context) {
    context = document.createElement('canvas').getContext('2d');
    if (!context) throw new Error('This browser cannot measure text on a canvas.');
  }
  context.font = `${weight} ${size}px ${FONT}`;
  return context.measureText(text).width;
}

/** the text cut short with "…" to fit the width */
export function fit(text: string, width: number, size: number, weight = 400): string {
  if (textWidth(text, size, weight) <= width) return text;
  let end = text.length;
  while (end > 0 && textWidth(`${text.slice(0, end)}…`, size, weight) > width) end--;
  return end ? `${text.slice(0, end).trimEnd()}…` : '';
}

/** the text broken into lines of at most the width, at spaces */
export function wrap(text: string, width: number, size: number): string[] {
  const lines: string[] = [];
  let line = '';
  for (const word of text.split(/\s+/).filter(Boolean)) {
    const next = line ? `${line} ${word}` : word;
    if (line && textWidth(next, size) > width) {
      lines.push(line);
      line = word;
    } else line = next;
  }
  if (line) lines.push(line);
  return lines;
}

export function escape(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

interface TextStyle {
  size: number;
  color?: string;
  weight?: number;
  anchor?: 'start' | 'middle' | 'end';
  /** in px */
  spacing?: number;
}

/** a line of text whose baseline sits at y */
export function text(x: number, y: number, content: string, style: TextStyle): string {
  const attributes = [
    `x="${round(x)}"`,
    `y="${round(y)}"`,
    `font-size="${style.size}"`,
    `fill="${style.color ?? INK}"`,
    style.weight && style.weight !== 400 ? `font-weight="${style.weight}"` : '',
    style.anchor && style.anchor !== 'start' ? `text-anchor="${style.anchor}"` : '',
    style.spacing ? `letter-spacing="${style.spacing}"` : '',
  ];
  return `<text ${attributes.filter(Boolean).join(' ')}>${escape(content)}</text>`;
}

/** the baseline of a line of `size` text centred in a box of `height` from `top` */
export function baseline(top: number, height: number, size: number): number {
  return top + height / 2 + size * 0.35;
}

export function rect(x: number, y: number, width: number, height: number, fill: string, extra = ''): string {
  return `<rect x="${round(x)}" y="${round(y)}" width="${round(Math.max(0, width))}" height="${round(height)}" fill="${fill}"${extra ? ` ${extra}` : ''}/>`;
}

export function line(x1: number, y1: number, x2: number, y2: number, stroke: string, extra = ''): string {
  return `<line x1="${round(x1)}" y1="${round(y1)}" x2="${round(x2)}" y2="${round(y2)}" stroke="${stroke}"${extra ? ` ${extra}` : ''}/>`;
}

export function round(value: number): number {
  return Math.round(value * 10) / 10;
}

/** the hatches of the "Other" bar, as in RankedTable */
export const HATCHES =
  '<defs>' +
  `<pattern id="hatch" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(45)">${rect(0, 0, 5, 5, ACCENT_TINT)}${rect(0, 0, 2, 5, ACCENT)}</pattern>` +
  `<pattern id="hatch-muted" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(45)">${rect(0, 0, 5, 5, '#f5f5f5')}${rect(0, 0, 2, 5, '#9e9e9e')}</pattern>` +
  '</defs>';

/** an ECharts option drawn by ECharts itself, without animation or tooltip */
export function drawECharts(option: EChartsOption, width: number, height: number): Drawing {
  const chart = init(null, null, { renderer: 'svg', ssr: true, width, height });
  chart.setOption({ ...option, animation: false });
  const svg = chart.renderToSVGString();
  chart.dispose();
  return { svg, height };
}

/** the image's width and its margins, in px */
export const IMAGE_WIDTH = 1000;
const MARGIN = 48;
export const CONTENT_WIDTH = IMAGE_WIDTH - 2 * MARGIN;

interface Page {
  eyebrow: string;
  title: string;
  note: string;
  drawings: Drawing[];
  legend: LegendItem[];
  footer: string[];
}

/** the whole image: the heading, the drawings one under the other, the legend and the footer */
export function composeImage(page: Page): { svg: string; width: number; height: number } {
  const parts: string[] = [];
  let y = MARGIN;

  parts.push(text(MARGIN, y + 13, page.eyebrow.toUpperCase(), { size: 13, spacing: 0.26 }));
  y += 13 + 14;
  for (const titleLine of wrap(page.title, CONTENT_WIDTH, 24)) {
    parts.push(text(MARGIN, baseline(y, 31, 24), titleLine, { size: 24 }));
    y += 31;
  }
  if (page.note) {
    y += 6;
    for (const noteLine of wrap(page.note, CONTENT_WIDTH * 0.75, 14)) {
      parts.push(text(MARGIN, baseline(y, 20, 14), noteLine, { size: 14, color: GREY_8 }));
      y += 20;
    }
  }
  y += 36;

  for (const drawing of page.drawings) {
    parts.push(`<g transform="translate(${MARGIN} ${round(y)})">${drawing.svg}</g>`);
    y += drawing.height + 24;
  }

  if (page.legend.length) {
    let x = MARGIN;
    for (const item of page.legend) {
      const label = item.detail ? `${item.label} ${item.detail}` : item.label;
      const width = 12 + 6 + textWidth(label, 13) + 24;
      if (x > MARGIN && x + width > MARGIN + CONTENT_WIDTH) {
        x = MARGIN;
        y += 22;
      }
      parts.push(rect(x, y + 4, 12, 12, item.color));
      parts.push(text(x + 18, baseline(y, 20, 13), item.label, { size: 13, color: GREY_9 }));
      if (item.detail)
        parts.push(
          text(x + 18 + textWidth(`${item.label} `, 13), baseline(y, 20, 13), item.detail, { size: 13, color: GREY_7 }),
        );
      x += width;
    }
    y += 20 + 24;
  }

  y += 8;
  parts.push(line(MARGIN, y, MARGIN + CONTENT_WIDTH, y, GREY_4));
  y += 14;
  for (const footerLine of page.footer.flatMap((entry) => wrap(entry, CONTENT_WIDTH, 12))) {
    parts.push(text(MARGIN, baseline(y, 18, 12), footerLine, { size: 12, color: GREY_7 }));
    y += 18;
  }
  const height = Math.ceil(y + MARGIN - 8);

  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${IMAGE_WIDTH}" height="${height}" viewBox="0 0 ${IMAGE_WIDTH} ${height}" font-family="${FONT}">` +
    HATCHES +
    rect(0, 0, IMAGE_WIDTH, height, 'white') +
    parts.join('') +
    '</svg>';
  return { svg, width: IMAGE_WIDTH, height };
}

/** the SVG rasterized, `scale` pixels for each of its px */
export async function toPng(svg: string, width: number, height: number, scale = 2): Promise<Blob> {
  const image = new Image();
  image.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  await image.decode();
  const canvas = document.createElement('canvas');
  canvas.width = width * scale;
  canvas.height = height * scale;
  const painter = canvas.getContext('2d');
  if (!painter) throw new Error('This browser cannot draw on a canvas.');
  painter.drawImage(image, 0, 0, canvas.width, canvas.height);
  return new Promise((resolve, reject) =>
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error('The PNG could not be made.'))), 'image/png'),
  );
}

/** hands the file to the browser, as a download */
export function save(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  // the download starts from the click: the link can go after it
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

/** "iaq-database-datasets-by-country-2026-11-26.png" */
export function fileName(eyebrow: string, format: 'png' | 'svg', date: Date): string {
  const slug = eyebrow
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 60)
    .replace(/-$/, '');
  const day = [date.getFullYear(), date.getMonth() + 1, date.getDate()].map((n) => String(n).padStart(2, '0'));
  return `iaq-database-${slug}-${day.join('-')}.${format}`;
}
