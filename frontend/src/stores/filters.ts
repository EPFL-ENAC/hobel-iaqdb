import { defineStore } from 'pinia';

export type FilterParams = {
  construction_years?: [number, number];
  altitudes?: [number, number];
  climate_zones?: string[] | null;
  building_types?: string[] | null;
  age_groups?: string[] | null;
  outdoor_envs?: string[] | null;
  mechanical_ventilation?: string | null;
  mechanical_ventilation_types?: string[] | null;
  study_ids: number[] | null;
};

export const DEFAULT_CONSTRUCTION_YEARS = { min: 1900, max: new Date().getFullYear() };
export const DEFAULT_ALTITUDES = { min: 0, max: 2500 };

export const useFiltersStore = defineStore(
  'filters',
  () => {
    const construction_years = ref({ ...DEFAULT_CONSTRUCTION_YEARS });
    const altitudes = ref({ ...DEFAULT_ALTITUDES });
    const climate_zones = ref<string[]>([]);
    const building_types = ref<string[]>([]);
    const age_groups = ref<string[]>([]);
    const outdoor_envs = ref<string[]>([]);
    const mechanical_ventilation = ref<string | null>(null);
    const mechanical_ventilation_types = ref<string[]>([]);

    const updates = ref(0);

    function reset() {
      construction_years.value = { ...DEFAULT_CONSTRUCTION_YEARS };
      altitudes.value = { ...DEFAULT_ALTITUDES };
      climate_zones.value = [];
      building_types.value = [];
      age_groups.value = [];
      outdoor_envs.value = [];
      mechanical_ventilation.value = null;
      mechanical_ventilation_types.value = [];
    }

    function notifyUpdate() {
      updates.value = updates.value + 1;
    }

    function asParams(): FilterParams {
      return {
        construction_years: [
          construction_years.value.min,
          construction_years.value.max,
        ],
        altitudes: [altitudes.value.min, altitudes.value.max],
        climate_zones: climate_zones.value ? [...climate_zones.value] : [],
        building_types: building_types.value ? [...building_types.value] : [],
        age_groups: age_groups.value ? [...age_groups.value] : [],
        outdoor_envs: outdoor_envs.value ? [...outdoor_envs.value] : [],
        mechanical_ventilation: mechanical_ventilation.value,
        mechanical_ventilation_types: mechanical_ventilation_types.value ? [...mechanical_ventilation_types.value] : [],
        study_ids: [],
      };
    }

    return {
      construction_years,
      altitudes,
      climate_zones,
      building_types,
      age_groups,
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
