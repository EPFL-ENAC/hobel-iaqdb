/**
 * The scatter of a relationship chart: the dots, the least-squares line over
 * their x extent, and an optional reference line. The pair chart, "Explore
 * pollutant patterns" and each small chart of a split draw with it.
 */
import type { EChartsOption } from 'echarts';
import { FIGURE_ACCENT, FIGURE_GAP, GRID, MUTED, niceTicks } from '@/components/plots/charts';
import type { ExploreBucket } from '@/models';

type Fit = ExploreBucket['fit'];

/** An axis range, the same for every small chart of a split. */
export interface AxisRange {
  min: number;
  max: number;
  interval: number;
}

/** How a chart draws its dots and its y axis. */
export interface ScatterStyle {
  dot: number;
  opacity: number;
  yTicks: number;
}

export interface ScatterSpec {
  points: [number, number][];
  fit: Fit;
  style: ScatterStyle;
  formatX: (value: number) => string;
  formatY: (value: number) => string;
  /** x from zero when no value is negative: true for concentrations, not for years */
  xZero: boolean;
  /** the tooltip of a dot */
  tooltip: (x: number, y: number) => string;
  /** titles at the ends of the axes */
  names?: { x: string; y: string } | undefined;
  /** a horizontal line, with its label when there is room for it */
  reference?: { value: number; label?: string | undefined } | undefined;
  /** the axis ranges shared by the small charts of a split */
  ranges?: { x: AxisRange; y: AxisRange } | undefined;
}

/**
 * The range of `values` on nice ticks, from zero when none is negative and
 * `zero` is asked: concentrations stay on the positive side.
 */
export function rangeOf(values: number[], ticks: number, zero: boolean): AxisRange {
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const steps = niceTicks(zero && lo >= 0 ? 0 : lo, hi, ticks);
  const first = steps[0] ?? lo;
  const last = steps[steps.length - 1] ?? hi;
  const second = steps[1];
  return {
    min: first,
    max: last,
    interval: second === undefined ? last - first || 1 : second - first,
  };
}

/** The least-squares line over the x extent of the dots; none without a fit. */
function trendLine(points: [number, number][], fit: Fit): [number, number][] {
  if (fit?.slope == null || fit.intercept == null || !points.length) return [];
  const xs = points.map(([x]) => x);
  const lo = Math.min(...xs);
  const hi = Math.max(...xs);
  return [
    [lo, fit.slope * lo + fit.intercept],
    [hi, fit.slope * hi + fit.intercept],
  ];
}

/** Without shared ranges: from zero for positive values, the reference in view. */
function ownRange(spec: ScatterSpec, axis: 'x' | 'y'): Record<string, unknown> {
  const shared = spec.ranges?.[axis];
  if (shared) return { ...shared };
  const values = spec.points.map(([x, y]) => (axis === 'x' ? x : y));
  const zero = Math.min(...values) >= 0 && (axis === 'y' || spec.xZero);
  const reference = axis === 'y' ? spec.reference?.value : undefined;
  return {
    ...(zero ? { min: 0 } : {}),
    ...(reference !== undefined
      ? {
          max: (extent: { max: number }) => Math.max(extent.max, reference * 1.1),
        }
      : {}),
  };
}

function referenceLine(reference: ScatterSpec['reference']) {
  if (!reference) return {};
  const { label } = reference;
  return {
    markLine: {
      silent: true,
      symbol: 'none',
      lineStyle: { color: FIGURE_GAP, type: 'solid' as const, width: 1.5 },
      label: label
        ? {
            position: 'insideEndTop' as const,
            distance: 6,
            padding: [2, 0, 4, 0],
            lineHeight: 16,
            color: FIGURE_GAP,
            fontSize: 11,
            formatter: label,
          }
        : { show: false },
      data: [{ yAxis: reference.value }],
    },
  };
}

export function scatterOption(spec: ScatterSpec): EChartsOption {
  if (!spec.points.length) return {};
  const line = trendLine(spec.points, spec.fit);
  const axisLabel = { color: MUTED, fontSize: 11 };
  const names = spec.names;
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const item = Array.isArray(p) ? p[0] : p;
        if (!item || item.seriesType !== 'scatter') return '';
        const [x, y] = item.value as [number, number];
        return spec.tooltip(x, y);
      },
    },
    grid: names
      ? { left: 0, right: 16, top: 28, bottom: 24, containLabel: true }
      : { left: 0, right: 8, top: 16, bottom: 0, containLabel: true },
    xAxis: {
      type: 'value',
      scale: true,
      ...ownRange(spec, 'x'),
      ...(names
        ? {
            name: `${names.x} →`,
            nameLocation: 'end' as const,
            nameGap: 8,
            nameTextStyle: {
              color: MUTED,
              fontSize: 11,
              align: 'right',
              verticalAlign: 'top',
              padding: [14, 0, 0, 0],
            },
          }
        : {}),
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel: { ...axisLabel, formatter: (v: number) => spec.formatX(v) },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      scale: true,
      ...ownRange(spec, 'y'),
      splitNumber: spec.style.yTicks,
      ...(names
        ? {
            name: `↑ ${names.y}`,
            nameLocation: 'end' as const,
            nameGap: 12,
            nameTextStyle: { color: MUTED, fontSize: 11, align: 'left' },
          }
        : {}),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { ...axisLabel, formatter: (v: number) => spec.formatY(v) },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: [
      {
        type: 'scatter',
        data: spec.points,
        symbolSize: spec.style.dot,
        itemStyle: { color: FIGURE_ACCENT, opacity: spec.style.opacity },
        cursor: 'default',
        clip: false,
        ...referenceLine(spec.reference),
      },
      ...(line.length
        ? [
            {
              type: 'line' as const,
              data: line,
              symbol: 'none',
              silent: true,
              lineStyle: { color: '#212121', width: 1.5 },
            },
          ]
        : []),
    ],
  };
}

/**
 * The axis ranges of the small charts of a split: every dot of every group in
 * view, and the reference.
 */
export function splitRanges(
  buckets: ExploreBucket[],
  options: { xZero: boolean; yTicks: number; reference?: number | undefined },
): { x: AxisRange; y: AxisRange } | undefined {
  const points = buckets.flatMap((b) => b.points ?? []);
  if (!points.length) return undefined;
  const ys = points.map(([, y]) => y);
  if (options.reference !== undefined) ys.push(options.reference * 1.1);
  return {
    x: rangeOf(
      points.map(([x]) => x),
      4,
      options.xZero,
    ),
    y: rangeOf(ys, options.yTicks, true),
  };
}
