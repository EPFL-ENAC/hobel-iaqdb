import { defineStore } from 'pinia';
import { api } from 'src/boot/api';
import { Study, Building, Room, StudiesResult, BuildingsResult, RoomsResult } from 'src/models';

export const useCatalogStore = defineStore('catalog', () => {

  const study = ref<Study>();
  const buildings = ref<Building[]>([]);
  const rooms = ref<Room[]>([]);

  const filterStore = useFiltersStore();

  async function loadStudies(skip: number, limit: number): Promise<StudiesResult> {
    return api.get('/catalog/studies',{
      params: {
        range: JSON.stringify([skip, limit + skip - 1]),
        filter: JSON.stringify(getFilterParams())
      },
      paramsSerializer: {
        indexes: null, // no brackets at all
      }
    }).then((response) => response.data)
  }

  async function loadBuildings(skip: number, limit: number): Promise<BuildingsResult> {
    return api.get('/catalog/buildings', { 
      params: {
        range: JSON.stringify([skip, limit + skip - 1]),
        filter: JSON.stringify(getFilterParams())
      },
      paramsSerializer: {
        indexes: null, // no brackets at all
      }
    }).then((response) => response.data)
  }

  async function loadSpaces(skip: number, limit: number): Promise<RoomsResult> {
    return api.get('/catalog/spaces', { 
      params: {
        range: JSON.stringify([skip, limit + skip - 1]),
        filter: JSON.stringify(getFilterParams())
      },
      paramsSerializer: {
        indexes: null, // no brackets at all
      }
    }).then((response) => response.data)
  }

  function getFilterParams() {
    const altitudes = filterStore.altitudes;
    return {
      $building: {
        altitude: [altitudes.min, altitudes.max],
        climate_zone: filterStore.climateZones,
      },
      $space: {
        ventilations: filterStore.ventilations,
      }
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
    loadSpaces,
    loadStudy,
    study,
    buildings,
    rooms
  }

});