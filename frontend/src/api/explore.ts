/**
 * Explore charts API (`/stats/*`): one parameter contract, one envelope.
 * The filter sent to every route is built here, once, from the filters
 * store, so the map, the lists and the charts agree.
 */
import { api } from '@/boot/api';
import type { ExploreFilter, ExploreParams, ExploreResult, ExploreSchema } from '@/models';
import {
  DEFAULT_ALTITUDES,
  DEFAULT_CONSTRUCTION_YEARS,
  DEFAULT_MEASUREMENT_YEARS,
  useFiltersStore,
} from '@/stores/filters';
import { withRange } from '@/utils/numbers';

export type ExploreRoute = 'metadata' | 'measurements' | 'relationships';

function nonEmpty(values: string[] | null | undefined): string[] | undefined {
  return values && values.length ? [...values].sort() : undefined;
}

export function studyCriteria() {
  const filters = useFiltersStore();
  return { identifier: nonEmpty(filters.study_ids) };
}

export function buildingCriteria() {
  const filters = useFiltersStore();
  const constructionYears = withRange(
    [filters.construction_years.min, filters.construction_years.max],
    [DEFAULT_CONSTRUCTION_YEARS.min, DEFAULT_CONSTRUCTION_YEARS.max],
  )
    ? [
        { construction_year: { $gte: filters.construction_years.min } },
        { construction_year: { $lte: filters.construction_years.max } },
      ]
    : [];
  const altitudes = withRange(
    [filters.altitudes.min, filters.altitudes.max],
    [DEFAULT_ALTITUDES.min, DEFAULT_ALTITUDES.max],
  )
    ? [{ altitude: { $gte: filters.altitudes.min } }, { altitude: { $lte: filters.altitudes.max } }]
    : [];
  // the store keeps cities as "City, CC"
  const cities = (filters.cities || []).map((city) => city.substring(0, city.length - 4));
  return {
    $and: constructionYears.length || altitudes.length ? [...constructionYears, ...altitudes] : undefined,
    type: nonEmpty(filters.building_types),
    country: nonEmpty(filters.countries),
    city: nonEmpty(cities),
    socioeconomic_status: nonEmpty(filters.socioeconomic_status),
    age_group: nonEmpty(filters.age_groups),
    outdoor_env: nonEmpty(filters.outdoor_envs),
    mechanical_ventilation: filters.mechanical_ventilation || undefined,
    climate_zone: nonEmpty(filters.climate_zones),
  };
}

export function spaceCriteria() {
  const filters = useFiltersStore();
  return { mechanical_ventilation_type: nonEmpty(filters.mechanical_ventilation_types) };
}

/** The study-anchored filter every explore route takes. */
export function exploreFilter(): ExploreFilter {
  return {
    ...studyCriteria(),
    $building: buildingCriteria(),
    $space: spaceCriteria(),
  };
}

/**
 * The measurement time range, as `from` (inclusive) and `to` (exclusive)
 * dates: whole years, none at the default bounds. Only the measurement
 * routes filter rows by it.
 */
export function exploreRange(): Pick<ExploreParams, 'from' | 'to'> {
  const { min, max } = useFiltersStore().measurement_years;
  if (!withRange([min, max], [DEFAULT_MEASUREMENT_YEARS.min, DEFAULT_MEASUREMENT_YEARS.max])) return {};
  return {
    ...(min > DEFAULT_MEASUREMENT_YEARS.min ? { from: `${min}-01-01` } : {}),
    ...(max < DEFAULT_MEASUREMENT_YEARS.max ? { to: `${max + 1}-01-01` } : {}),
  };
}

function sortedJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(sortedJson).join(',')}]`;
  if (value && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
      .filter(([, v]) => v !== undefined)
      .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
    return `{${entries.map(([k, v]) => `${JSON.stringify(k)}:${sortedJson(v)}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

/** Query string values, canonical: sorted keys, no undefined, sorted lists. */
export function canonicalParams(params: ExploreParams): Record<string, string> {
  const out: Record<string, string> = {};
  const entries = Object.entries(params).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  for (const [key, value] of entries) {
    if (value === undefined || value === null) continue;
    if (key === 'filter') {
      out.filter = sortedJson(value);
    } else if (Array.isArray(value)) {
      // `by` keeps its order (it is the order of bucket keys)
      const items = key === 'by' ? value : [...value].sort();
      if (items.length) out[key] = items.join(',');
    } else {
      out[key] = String(value);
    }
  }
  return out;
}

export function canonicalKey(route: ExploreRoute | 'schema', params: ExploreParams): string {
  return `${route}?${new URLSearchParams(canonicalParams(params)).toString()}`;
}

function config(params?: Record<string, string>, signal?: AbortSignal) {
  return { ...(params ? { params } : {}), ...(signal ? { signal } : {}) };
}

export async function schema(signal?: AbortSignal): Promise<ExploreSchema> {
  return api.get('/stats/schema', config(undefined, signal)).then((response) => response.data as ExploreSchema);
}

export async function query(
  route: ExploreRoute,
  params: ExploreParams,
  signal?: AbortSignal,
): Promise<ExploreResult> {
  return api
    .get(`/stats/${route}`, config(canonicalParams(params), signal))
    .then((response) => response.data as ExploreResult);
}

export const metadata = (params: ExploreParams, signal?: AbortSignal) => query('metadata', params, signal);
export const measurements = (params: ExploreParams, signal?: AbortSignal) =>
  query('measurements', params, signal);
export const relationships = (params: ExploreParams, signal?: AbortSignal) =>
  query('relationships', params, signal);
