import type { SetOptionOpts } from 'echarts';
import type { Router } from 'vue-router';
import type {
  ExploreBenchmark,
  ExploreBucket,
  ExploreDimension,
  ExploreParams,
  ExploreResult,
  ExploreSchema,
} from '@/models';
import { useExploreStore } from '@/stores/explore';
import { useFiltersStore } from '@/stores/filters';
import {
  buildingTypeOptions,
  climateOptions,
  countryOptions,
  mechanicalVentilationTypeOptions,
  spaceTypeOptions,
  yesNoOptions,
  type OptionItem,
} from '@/utils/options';

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

/** A benchmark from the schema, or a stand-in until one is provided. */
export type Benchmark = Pick<ExploreBenchmark, 'source' | 'averaging' | 'value' | 'unit' | 'note'> & {
  placeholder?: boolean;
};

/**
 * Stand-ins for pollutants the database has no benchmark for yet; charts show
 * them with a "placeholder" badge until the reference values are provided.
 */
const PLACEHOLDER_BENCHMARKS: Record<string, Benchmark> = {
  co2: {
    source: 'Placeholder',
    averaging: 'day',
    value: 800,
    unit: 'ppm',
    note: 'target',
    placeholder: true,
  },
};

/** The first benchmark the schema lists for a pollutant, else its placeholder. */
export function benchmarkOf(schema: ExploreSchema | null, slug: string | null): Benchmark | null {
  if (!slug) return null;
  const listed = schema?.parameters.find((p) => p.slug === slug)?.benchmarks[0];
  return listed ?? PLACEHOLDER_BENCHMARKS[slug] ?? null;
}

/** 463 → 450 (floor) or 500 (ceil): a readable axis bound, to half a magnitude. */
export function roundBound(value: number, round: (v: number) => number): number {
  const step = 10 ** Math.floor(Math.log10(Math.abs(value) || 1)) / 2;
  return round(value / step) * step;
}

/** Keys that name no category: missing, or coded as unknown / not applicable (any case). */
const UNKNOWN_KEYS = new Set(['unknown', 'na']);

export function isUnknownKey(key: string | null | undefined): boolean {
  return key === null || key === undefined || UNKNOWN_KEYS.has(key.toLowerCase());
}

/** The contexts a statistics chart can compare, in menu order. */
export const STATS_CONTEXTS = [
  'country',
  'city',
  'climate_zone',
  'building_type',
  'ventilation',
  'ventilation_type',
  'space_type',
];

/** Label lists for the dimensions whose keys are codes. */
const KEY_OPTIONS: Record<string, OptionItem[]> = {
  country: countryOptions,
  climate_zone: climateOptions,
  building_type: buildingTypeOptions,
  ventilation: yesNoOptions,
  ventilation_type: mechanicalVentilationTypeOptions,
  space_type: spaceTypeOptions,
};

/**
 * Human label of a bucket key: the study name for studies, the option label
 * for coded dimensions, the key itself otherwise.
 */
export function keyLabel(dimension: string, key: string): string {
  if (dimension === 'study') return useExploreStore().studyNames.get(key) || key;
  return KEY_OPTIONS[dimension]?.find((opt) => opt.value === key)?.label || key;
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
