import { defineStore } from 'pinia';
import { api } from 'src/boot/api';
import { Study, Building, Room, StudiesResult, BuildingsResult, RoomsResult } from 'src/models';
import { DEFAULT_ALTITUDES } from 'src/stores/filters';


export const useCatalogStore = defineStore('catalog', () => {

  const study = ref<Study>();
  const buildings = ref<Building[]>([]);
  const rooms = ref<Room[]>([]);

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
      climates: filterStore.climateZones,
      ventilations: filterStore.ventilations,
    }
  }

  async function loadStudy(id: string) {
    // 66866e82e2a2c5f0504c88f2
    return api.get(`/catalog/study/${id}`).then((response) => {
      study.value = response.data;
      return Promise.all([
        loadStudyBuildings(),
        loadStudyRooms()
      ]);
    });
  }

  async function loadStudyBuildings() {
    buildings.value = [];
    return api.get(`/catalog/study/${study.value?._id}/buildings`).then((response) => {
      buildings.value = response.data;
    })
  }

  async function loadStudyRooms() {
    rooms.value = [];
    return api.get(`/catalog/study/${study.value?._id}/rooms`).then((response) => {
      rooms.value = response.data;
    })
  }

  return {
    loadStudies,
    loadBuildings,
    loadRooms,
    loadStudy,
    study,
    buildings,
    rooms
  }

});