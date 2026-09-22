import type { SetOptionOpts } from 'echarts';
import type { Router } from 'vue-router';
import type { ExploreBucket, ExploreDimension, ExploreParams, ExploreResult } from '@/models';
import { useFiltersStore } from '@/stores/filters';

export const initOptions: InitOptions = {
  renderer: 'svg',
};
export const updateOptions: SetOptionOpts = {
  notMerge: true,
};

/**
 * https://echarts.apache.org/en/api.html#echarts.init
 */
interface InitOptions {
  renderer: 'canvas' | 'svg';
}

export interface SeriesPoint {
  key: string | null;
  value: number;
  bucket: ExploreBucket;
}

export interface Series {
  key: string | null;
  data: SeriesPoint[];
}

/**
 * Buckets to ECharts-ready series. With one dimension there is one series;
 * with two, one series per value of `seriesDimension` and points keyed by
 * the other dimension. `value` picks the number a chart plots (default n).
 */
export function toSeries(
  result: ExploreResult,
  seriesDimension = 1,
  value: (bucket: ExploreBucket) => number = (bucket) => bucket.n,
): Series[] {
  if (result.meta.dimensions.length < 2) {
    return [
      {
        key: null,
        data: result.buckets.map((bucket) => ({ key: bucket.key[0] ?? null, value: value(bucket), bucket })),
      },
    ];
  }
  const pointDimension = seriesDimension === 0 ? 1 : 0;
  const series = new Map<string | null, Series>();
  for (const bucket of result.buckets) {
    const seriesKey = bucket.key[seriesDimension] ?? null;
    let entry = series.get(seriesKey);
    if (!entry) {
      entry = { key: seriesKey, data: [] };
      series.set(seriesKey, entry);
    }
    entry.data.push({ key: bucket.key[pointDimension] ?? null, value: value(bucket), bucket });
  }
  return [...series.values()];
}

export type ClickKind = 'filter' | 'drill' | 'navigate';

export interface ChartClick {
  kind: ClickKind;
  /** the dimension the clicked bucket key belongs to */
  dimension: ExploreDimension;
  /** the request the chart is showing (drill merges into a copy of it) */
  params: ExploreParams;
  /** index of the dimension in bucket.key */
  keyIndex?: number;
  router?: Router;
}

/** Global filter fields a dimension's filter_path maps to. */
const FILTER_TARGETS: Record<string, (value: string) => void> = {
  identifier: (value) => push(useFiltersStore().study_ids, value),
  '$building.country': (value) => push(useFiltersStore().countries, value),
  '$building.city': (value) => push(useFiltersStore().cities, value),
  '$building.climate_zone': (value) => push(useFiltersStore().climate_zones, value),
  '$building.type': (value) => push(useFiltersStore().building_types, value),
  '$building.mechanical_ventilation': (value) => {
    useFiltersStore().mechanical_ventilation = value;
  },
  '$space.mechanical_ventilation_type': (value) =>
    push(useFiltersStore().mechanical_ventilation_types, value),
};

function push(list: string[], value: string) {
  if (!list.includes(value)) list.push(value);
}

/** Merge a bucket key into the request filter, following `filter_path`. */
export function refine(params: ExploreParams, dimension: ExploreDimension, key: string): ExploreParams {
  const path = dimension.filter_path;
  if (!path) throw new Error(`dimension ${dimension.key} cannot become a filter`);
  const next: ExploreParams = { ...params, filter: { ...(params.filter || {}) } };
  if (path === 'parameters') {
    next.parameters = [key];
    return next;
  }
  if (path === 'from') {
    next.from = key;
    next.to = nextPeriod(dimension.key, key);
    return next;
  }
  const filter = next.filter as Record<string, unknown>;
  if (path.startsWith('$')) {
    const [block, field] = path.split('.', 2);
    if (!block || !field) throw new Error(`malformed filter path ${path}`);
    filter[block] = { ...((filter[block]) || {}), [field]: key };
  } else {
    filter[path] = key;
  }
  return next;
}

function nextPeriod(dimension: string, key: string): string {
  const date = new Date(key);
  if (dimension === 'year') date.setUTCFullYear(date.getUTCFullYear() + 1);
  else if (dimension === 'month') date.setUTCMonth(date.getUTCMonth() + 1);
  else date.setUTCDate(date.getUTCDate() + 1);
  return date.toISOString().substring(0, 10);
}

/**
 * Every chart click is one of three declared kinds. `filter` pushes the
 * criterion into the global filters store (every chart, the map and the
 * lists re-query); `drill` returns the refined request with `by` set to
 * the next level; `navigate` opens the catalog view of the bucket.
 * Returns the drill request, or null for the other kinds.
 */
export function onBucketClick(chart: ChartClick, bucket: ExploreBucket): ExploreParams | null {
  const key = bucket.key[chart.keyIndex ?? 0];
  if (key === null || key === undefined) return null;
  if (chart.kind === 'filter') {
    const path = chart.dimension.filter_path;
    const target = path ? FILTER_TARGETS[path] : undefined;
    if (!target) throw new Error(`no global filter for dimension ${chart.dimension.key}`);
    target(key);
    useFiltersStore().notifyUpdate();
    return null;
  }
  if (chart.kind === 'drill') {
    if (!chart.dimension.drill_to) throw new Error(`dimension ${chart.dimension.key} has no drill level`);
    const next = refine(chart.params, chart.dimension, key);
    next.by = [chart.dimension.drill_to];
    return next;
  }
  if (!chart.router) throw new Error('navigate needs a router');
  if (chart.dimension.key === 'study') {
    void chart.router.push({ path: '/study', query: { id: key } });
  } else {
    const refined = refine(chart.params, chart.dimension, key);
    void chart.router.push({ path: '/data-hub', query: { filter: JSON.stringify(refined.filter) } });
  }
  return null;
}
