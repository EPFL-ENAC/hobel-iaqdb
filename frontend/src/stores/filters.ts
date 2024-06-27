import { defineStore } from 'pinia';

export type FilterParams = {
  altitudes: [number, number]
  climateZones: string[] | null
}

const DEFAULT_ALTITUDES = { min: 0, max: 2500 };

export const useFiltersStore = defineStore('filters', () => {

  const altitudes = ref({...DEFAULT_ALTITUDES});
  const climateZones = ref(null);

  function reset() {
    altitudes.value = {...DEFAULT_ALTITUDES};
    climateZones.value = null;
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
    reset,
    asParams,
  }

}, { persist: true });