import { defineStore } from 'pinia';

export type FilterParams = {
  altitudes?: [number, number];
  climateZones?: string[] | null;
  ventilations?: string[] | null;
  study_ids: number[] | null;
};

export const DEFAULT_ALTITUDES = { min: 0, max: 2500 };

export const useFiltersStore = defineStore(
  'filters',
  () => {
    const altitudes = ref({ ...DEFAULT_ALTITUDES });
    const climateZones = ref<string[]>([]);
    const ventilations = ref<string[]>([]);

    const updates = ref(0);

    function reset() {
      altitudes.value = { ...DEFAULT_ALTITUDES };
      climateZones.value = [];
      ventilations.value = [];
    }

    function notifyUpdate() {
      updates.value = updates.value + 1;
    }

    function asParams(): FilterParams {
      return {
        altitudes: [altitudes.value.min, altitudes.value.max],
        climateZones: climateZones.value ? [...climateZones.value] : [],
        ventilations: ventilations.value ? [...ventilations.value] : [],
        study_ids: [],
      };
    }

    return {
      altitudes,
      climateZones,
      ventilations,
      updates,
      reset,
      asParams,
      notifyUpdate,
    };
  },
  { persist: true },
);
