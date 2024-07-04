import { defineStore } from 'pinia';
import { api } from 'src/boot/api';
import { StudiesResult, BuildingsResult, RoomsResult } from 'src/models';
import { DEFAULT_ALTITUDES } from 'src/stores/filters';


export const useCatalogStore = defineStore('catalog', () => {

  const filterStore = useFiltersStore();

  async function loadStudies(skip: number, limit: number): Promise<StudiesResult> {
    const filters = getFilterParams();
    return api.get('/catalog/studies',{
      params: {
        skip,
        limit,
        ...filters
      },
      paramsSerializer: {
        indexes: null, // no brackets at all
      }
    }).then((response) => response.data)
  }

  async function loadBuildings(skip: number, limit: number): Promise<BuildingsResult> {
    const filters = getFilterParams();
    return api.get('/catalog/buildings', { 
      params: {
        skip,
        limit,
        ...filters
      },
      paramsSerializer: {
        indexes: null, // no brackets at all
      }
    }).then((response) => response.data)
  }

  async function loadRooms(skip: number, limit: number): Promise<RoomsResult> {
    const filters = getFilterParams();
    return api.get('/catalog/rooms', { 
      params: {
        skip,
        limit,
        ...filters
      },
      paramsSerializer: {
        indexes: null, // no brackets at all
      }
    }).then((response) => response.data)
  }

  function getFilterParams() {
    const altitudes = filterStore.altitudes;
    return {
      altmin: altitudes.min === DEFAULT_ALTITUDES.min ? undefined : altitudes.min,
      altmax: altitudes.max === DEFAULT_ALTITUDES.max ? undefined : altitudes.max,
      climates: filterStore.climateZones
    }
  }

  return {
    loadStudies,
    loadBuildings,
    loadRooms
  }

});