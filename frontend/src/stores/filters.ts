import { defineStore } from 'pinia';
import { withRange } from 'src/utils/numbers';

export type FilterParams = {
  countries?: string[] | null;
  cities?: string[] | null;
  construction_years?: [number, number];
  altitudes?: [number, number];
  climate_zones?: string[] | null;
  building_types?: string[] | null;
  age_groups?: string[] | null;
  socioeconomic_status?: string[] | null;
  outdoor_envs?: string[] | null;
  mechanical_ventilation?: string | null;
  mechanical_ventilation_types?: string[] | null;
  study_ids: string[] | null;
};

export const DEFAULT_CONSTRUCTION_YEARS = { min: 1800, max: new Date().getFullYear() };
export const DEFAULT_ALTITUDES = { min: 0, max: 2500 };

export const useFiltersStore = defineStore(
  'filters',
  () => {
    const countries = ref([]);
    const cities = ref([]);
    const construction_years = ref({ ...DEFAULT_CONSTRUCTION_YEARS });
    const altitudes = ref({ ...DEFAULT_ALTITUDES });
    const climate_zones = ref<string[]>([]);
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
      climate_zones.value = [];
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
        study_ids: [],
      };
    }

    return {
      countries,
      cities,
      construction_years,
      altitudes,
      climate_zones,
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
  { persist: true },
);
