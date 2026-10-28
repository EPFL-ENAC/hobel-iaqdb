import { defineStore, type StateTree } from 'pinia';
import { withRange } from '@/utils/numbers';

export type FilterParams = {
  countries?: string[] | null;
  cities?: string[] | null;
  construction_years?: [number, number] | undefined;
  altitudes?: [number, number] | undefined;
  climate_zones?: string[] | null;
  building_types?: string[] | null;
  age_groups?: string[] | null;
  socioeconomic_status?: string[] | null;
  outdoor_envs?: string[] | null;
  mechanical_ventilation?: string | null;
  mechanical_ventilation_types?: string[] | null;
  study_ids: string[] | null;
};

/** The filters as values: the store's, or a draft being edited before it is applied. */
export interface FilterFields {
  countries: string[];
  cities: string[];
  construction_years: { min: number; max: number };
  altitudes: { min: number; max: number };
  measurement_years: { min: number; max: number };
  climate_zones: string[];
  study_ids: string[];
  building_types: string[];
  age_groups: string[];
  socioeconomic_status: string[];
  outdoor_envs: string[];
  mechanical_ventilation: string | null;
  mechanical_ventilation_types: string[];
}

export const DEFAULT_CONSTRUCTION_YEARS = { min: 1800, max: new Date().getFullYear() };
export const DEFAULT_ALTITUDES = { min: 0, max: 2500 };
/** "All years": the first and last years holding records, once loaded (see setMeasurementYears) */
export const DEFAULT_MEASUREMENT_YEARS = reactive({ min: 2000, max: new Date().getFullYear() });

type YearRange = { min: number; max: number };

/**
 * A range moved from one pair of bounds to another: a bound at the old one
 * moves to the new one, still meaning "all years"; one set within them is
 * kept, clamped to them.
 */
export function rebound(range: YearRange, previous: YearRange, next: YearRange): YearRange {
  const clamp = (year: number) => Math.min(Math.max(year, next.min), next.max);
  return {
    min: range.min === previous.min ? next.min : clamp(range.min),
    max: range.max === previous.max ? next.max : clamp(range.max),
  };
}

/** the years a range keeps out, null where it is at the bound: what a request sends (see exploreRange) */
function setBounds(range: YearRange, bounds: YearRange): string {
  return `${range.min > bounds.min ? range.min : null}–${range.max < bounds.max ? range.max : null}`;
}

/**
 * Bound the measurement years by the years that hold records. The figures
 * reload only when the applied range then asks for other years: "all
 * years" stays "all years" whatever its bounds.
 */
export function setMeasurementYears(extent: YearRange): void {
  const filters = useFiltersStore();
  const before = setBounds(filters.measurement_years, DEFAULT_MEASUREMENT_YEARS);
  filters.measurement_years = rebound(filters.measurement_years, DEFAULT_MEASUREMENT_YEARS, extent);
  Object.assign(DEFAULT_MEASUREMENT_YEARS, extent);
  if (setBounds(filters.measurement_years, extent) !== before) filters.notifyUpdate();
}

/** The store keeps cities as "City, CC"; filters and bucket keys use the bare name. */
export function cityName(entry: string): string {
  return entry.substring(0, entry.length - 4);
}

/**
 * Ranges whose default bounds move: the current year, or the years holding
 * records. A bound at its default means "unbounded", so it is stored as null:
 * an untouched range saved last year must not become "until last year" once
 * the year turns, nor "from 2010" once older records are added.
 */
const YEAR_RANGES: Record<string, { min: number; max: number }> = {
  construction_years: DEFAULT_CONSTRUCTION_YEARS,
  measurement_years: DEFAULT_MEASUREMENT_YEARS,
};

function serialize(state: StateTree): string {
  const stored = { ...state };
  for (const [field, defaults] of Object.entries(YEAR_RANGES)) {
    const range = state[field] as { min: number; max: number } | undefined;
    if (!range) continue;
    stored[field] = {
      min: range.min === defaults.min ? null : range.min,
      max: range.max === defaults.max ? null : range.max,
    };
  }
  return JSON.stringify(stored);
}

function deserialize(value: string): StateTree {
  const state = JSON.parse(value) as StateTree;
  for (const [field, defaults] of Object.entries(YEAR_RANGES)) {
    const range = state[field] as { min: number | null; max: number | null } | undefined;
    if (!range) continue;
    state[field] = { min: range.min ?? defaults.min, max: range.max ?? defaults.max };
  }
  return state;
}

export const useFiltersStore = defineStore(
  'filters',
  () => {
    const countries = ref<string[]>([]);
    const cities = ref<string[]>([]);
    const construction_years = ref({ ...DEFAULT_CONSTRUCTION_YEARS });
    const altitudes = ref({ ...DEFAULT_ALTITUDES });
    const measurement_years = ref({ ...DEFAULT_MEASUREMENT_YEARS });
    const climate_zones = ref<string[]>([]);
    const study_ids = ref<string[]>([]);
    const building_types = ref<string[]>([]);
    const age_groups = ref<string[]>([]);
    const socioeconomic_status = ref<string[]>([]);
    const outdoor_envs = ref<string[]>([]);
    const mechanical_ventilation = ref<string | null>(null);
    const mechanical_ventilation_types = ref<string[]>([]);

    const updates = ref(0);

    function reset() {
      countries.value = [];
      cities.value = [];
      construction_years.value = { ...DEFAULT_CONSTRUCTION_YEARS };
      altitudes.value = { ...DEFAULT_ALTITUDES };
      measurement_years.value = { ...DEFAULT_MEASUREMENT_YEARS };
      climate_zones.value = [];
      study_ids.value = [];
      building_types.value = [];
      age_groups.value = [];
      socioeconomic_status.value = [];
      outdoor_envs.value = [];
      mechanical_ventilation.value = null;
      mechanical_ventilation_types.value = [];
    }

    function notifyUpdate() {
      updates.value = updates.value + 1;
    }

    function asParams(): FilterParams {
      const constructionsRange: [number, number] = [construction_years.value.min, construction_years.value.max];
      const altitudesRange: [number, number] = [altitudes.value.min, altitudes.value.max];
      return {
        countries: countries.value.length > 0 ? [...countries.value] : null,
        cities: cities.value.length > 0 ? [...cities.value] : null,
        construction_years: withRange(constructionsRange, [DEFAULT_CONSTRUCTION_YEARS.min, DEFAULT_CONSTRUCTION_YEARS.max]) ? constructionsRange : undefined,
        altitudes: withRange(altitudesRange, [DEFAULT_ALTITUDES.min, DEFAULT_ALTITUDES.max]) ? altitudesRange : undefined,
        climate_zones: climate_zones.value ? [...climate_zones.value] : [],
        building_types: building_types.value ? [...building_types.value] : [],
        age_groups: age_groups.value ? [...age_groups.value] : [],
        socioeconomic_status: socioeconomic_status.value ? [...socioeconomic_status.value] : [],
        outdoor_envs: outdoor_envs.value ? [...outdoor_envs.value] : [],
        mechanical_ventilation: mechanical_ventilation.value,
        mechanical_ventilation_types: mechanical_ventilation_types.value ? [...mechanical_ventilation_types.value] : [],
        study_ids: study_ids.value ? [...study_ids.value] : [],
      };
    }

    return {
      countries,
      cities,
      construction_years,
      altitudes,
      measurement_years,
      climate_zones,
      study_ids,
      building_types,
      age_groups,
      socioeconomic_status,
      outdoor_envs,
      mechanical_ventilation,
      mechanical_ventilation_types,
      updates,
      reset,
      asParams,
      notifyUpdate,
    };
  },
  { persist: { serializer: { serialize, deserialize } } },
);
