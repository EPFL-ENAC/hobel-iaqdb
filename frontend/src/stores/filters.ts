import { defineStore } from 'pinia';

export type FilterParams = {
  altitudes: [number, number]
  climateZones: string[] | null
}

export const DEFAULT_ALTITUDES = { min: 0, max: 2500 };

export const useFiltersStore = defineStore('filters', () => {

  const altitudes = ref({...DEFAULT_ALTITUDES});
  const climateZones = ref(null);

  const updates = ref(0);

  function reset() {
    altitudes.value = {...DEFAULT_ALTITUDES};
    climateZones.value = null;
  }

  function notifyUpdate() {
    updates.value = updates.value + 1;
  }

  function asParams(): FilterParams {
    return {
      altitudes: [altitudes.value.min, altitudes.value.max],
      climateZones: climateZones.value ? [...climateZones.value] : []
    }
  }

  return {
    altitudes,
    climateZones,
    updates,
    reset,
    asParams,
    notifyUpdate
  }

}, { persist: true });