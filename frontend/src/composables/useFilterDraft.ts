/**
 * The explore filters as a draft: a copy of the applied filters and
 * pollutants that the filter dialog edits, counts against and applies at
 * once. Grouped in the dialog's sections, each cleared on its own.
 */
import type { InjectionKey } from 'vue';
import {
  DEFAULT_ALTITUDES,
  DEFAULT_CONSTRUCTION_YEARS,
  DEFAULT_MEASUREMENT_YEARS,
  type FilterFields,
} from '@/stores/filters';

export interface FilterDraft extends FilterFields {
  /** the pollutants; none means every pollutant */
  parameters: string[];
}

export type FilterSection = 'what' | 'where' | 'buildings' | 'spaces' | 'people';

export const FILTER_SECTIONS: FilterSection[] = ['what', 'where', 'buildings', 'spaces', 'people'];

/** the fields each section edits and clears */
export const SECTION_FIELDS: Record<FilterSection, (keyof FilterDraft)[]> = {
  what: ['parameters', 'measurement_years'],
  where: ['countries', 'cities', 'climate_zones', 'altitudes'],
  buildings: ['building_types', 'study_ids', 'construction_years'],
  spaces: ['mechanical_ventilation', 'mechanical_ventilation_types'],
  people: ['outdoor_envs', 'age_groups', 'socioeconomic_status'],
};

/** the draft the dialog's sections edit */
export const FILTER_DRAFT: InjectionKey<FilterDraft> = Symbol('filter-draft');

/** No filter: every pollutant, anywhere, any time. */
export function defaultDraft(): FilterDraft {
  return {
    countries: [],
    cities: [],
    construction_years: { ...DEFAULT_CONSTRUCTION_YEARS },
    altitudes: { ...DEFAULT_ALTITUDES },
    measurement_years: { ...DEFAULT_MEASUREMENT_YEARS },
    climate_zones: [],
    study_ids: [],
    building_types: [],
    age_groups: [],
    socioeconomic_status: [],
    outdoor_envs: [],
    mechanical_ventilation: null,
    mechanical_ventilation_types: [],
    parameters: [],
  };
}

/** The applied filters and pollutants, copied: editing the draft leaves them as they are. */
export function appliedDraft(): FilterDraft {
  const filters = useFiltersStore();
  return {
    countries: [...filters.countries],
    cities: [...filters.cities],
    construction_years: { ...filters.construction_years },
    altitudes: { ...filters.altitudes },
    measurement_years: { ...filters.measurement_years },
    climate_zones: [...filters.climate_zones],
    study_ids: [...filters.study_ids],
    building_types: [...filters.building_types],
    age_groups: [...filters.age_groups],
    socioeconomic_status: [...filters.socioeconomic_status],
    outdoor_envs: [...filters.outdoor_envs],
    mechanical_ventilation: filters.mechanical_ventilation,
    mechanical_ventilation_types: [...filters.mechanical_ventilation_types],
    parameters: [...useExploreStore().parameters],
  };
}

/** Make the draft the applied filters: every chart, list and count reloads once. */
export function applyDraft(draft: FilterDraft): void {
  const filters = useFiltersStore();
  const { parameters, ...fields } = copyOf(draft);
  Object.assign(filters, fields);
  useExploreStore().parameters = parameters;
  filters.notifyUpdate();
}

/** Put a section's fields back to their defaults, in place. */
export function clearSection(draft: FilterDraft, section: FilterSection): void {
  const defaults = defaultDraft();
  for (const field of SECTION_FIELDS[section]) Object.assign(draft, { [field]: defaults[field] });
}

/** A plain deep copy, read through the draft: a computed or watcher that copies tracks every field. */
function copyOf(draft: FilterDraft): FilterDraft {
  return JSON.parse(JSON.stringify(draft)) as FilterDraft;
}

/** A copy of the draft without these fields: a facet counts under every filter but its own. */
export function without(draft: FilterDraft, fields: (keyof FilterDraft)[]): FilterDraft {
  const defaults = defaultDraft();
  const copy = copyOf(draft);
  for (const field of fields) Object.assign(copy, { [field]: defaults[field] });
  return copy;
}

function sameRange(a: { min: number; max: number }, b: { min: number; max: number }): boolean {
  return a.min === b.min && a.max === b.max;
}

/** How many criteria of a section differ from their defaults; pollutants count as one. */
export function activeCount(draft: FilterDraft, section: FilterSection): number {
  const defaults = defaultDraft();
  let count = 0;
  for (const field of SECTION_FIELDS[section]) {
    const value = draft[field];
    const fallback = defaults[field];
    if (Array.isArray(value)) {
      if (field === 'parameters') count += value.join() === (fallback as string[]).join() ? 0 : 1;
      else count += value.length;
    } else if (value && typeof value === 'object') {
      count += sameRange(value, fallback as { min: number; max: number }) ? 0 : 1;
    } else if (value !== fallback) {
      count += 1;
    }
  }
  return count;
}
