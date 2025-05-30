import { defineStore } from 'pinia';
import { api } from 'src/boot/api';
import {
  Study,
  Building,
  Space,
  Instrument,
  Dataset,
  StudiesResult,
  BuildingsResult,
  SpacesResult,
  StudySummariesResult,
} from 'src/models';
import { DEFAULT_ALTITUDES, DEFAULT_CONSTRUCTION_YEARS } from './filters';
import { withRange } from 'src/utils/numbers';

export const useCatalogStore = defineStore('catalog', () => {
  const authStore = useAuthStore();
  const filterStore = useFiltersStore();

  const study = ref<Study>();
  const buildings = ref<Building[]>([]);
  const spaces = ref<Space[]>([]);
  const instruments = ref<Instrument[]>([]);
  const datasets = ref<Dataset[]>([]);
  const showStudyDetails = ref(false);
  
  async function loadStudySummaries(
    skip: number,
    limit: number,
  ): Promise<StudySummariesResult> {
    return api
      .get('/catalog/study-summaries', {
        params: {
          range: JSON.stringify([skip, limit + skip - 1]),
          filter: JSON.stringify(getFilterParams()),
        },
        paramsSerializer: {
          indexes: null, // no brackets at all
        },
      })
      .then((response) => response.data);
  }

  async function loadStudies(
    skip: number,
    limit: number,
  ): Promise<StudiesResult> {
    return api
      .get('/catalog/studies', {
        params: {
          range: JSON.stringify([skip, limit + skip - 1]),
          filter: JSON.stringify(getFilterParams()),
        },
        paramsSerializer: {
          indexes: null, // no brackets at all
        },
      })
      .then((response) => response.data);
  }

  async function loadBuildings(
    skip: number,
    limit: number,
  ): Promise<BuildingsResult> {
    return api
      .get('/catalog/buildings', {
        params: {
          range: JSON.stringify([skip, limit + skip - 1]),
          filter: JSON.stringify(getFilterParams()),
        },
        paramsSerializer: {
          indexes: null, // no brackets at all
        },
      })
      .then((response) => response.data);
  }

  async function loadSpaces(
    skip: number,
    limit: number,
  ): Promise<SpacesResult> {
    return api
      .get('/catalog/spaces', {
        params: {
          range: JSON.stringify([skip, limit + skip - 1]),
          filter: JSON.stringify(getFilterParams()),
        },
        paramsSerializer: {
          indexes: null, // no brackets at all
        },
      })
      .then((response) => response.data);
  }

  function getFilterParams() {
    const construction_years = withRange(
      [filterStore.construction_years.min, filterStore.construction_years.max], 
      [DEFAULT_CONSTRUCTION_YEARS.min, DEFAULT_CONSTRUCTION_YEARS.max]) ? [
      { construction_year: { $gte: filterStore.construction_years.min } },
      { construction_year: { $lte: filterStore.construction_years.max } },
    ] : [];
    const altitudes = withRange(
      [filterStore.altitudes.min, filterStore.altitudes.max], 
      [DEFAULT_ALTITUDES.min, DEFAULT_ALTITUDES.max]) ? [
      { altitude: { $gte: filterStore.altitudes.min } },
      { altitude: { $lte: filterStore.altitudes.max } },
    ] : [];
    return {
      $building: {
        $and: [
          ...construction_years,
          ...altitudes,
        ],
        type:
          filterStore.building_types && filterStore.building_types.length
            ? filterStore.building_types
            : undefined,
        age_group:
          filterStore.age_groups && filterStore.age_groups.length
            ? filterStore.age_groups
            : undefined,
        outdoor_env:
          filterStore.outdoor_envs && filterStore.outdoor_envs.length
            ? filterStore.outdoor_envs
            : undefined,
        mechanical_ventilation:
          filterStore.mechanical_ventilation || undefined,
        climate_zone:
          filterStore.climate_zones && filterStore.climate_zones.length
            ? filterStore.climate_zones
            : undefined,
      },
      $space: {
        mechanical_ventilation_type:
          filterStore.mechanical_ventilation_types && filterStore.mechanical_ventilation_types.length
            ? filterStore.mechanical_ventilation_types
            : undefined,
      },
    };
  }

  async function deleteStudy(id: string) {
    if (!authStore.isAuthenticated) return Promise.reject('Not authenticated');
    return authStore.updateToken().then(() => 
      api.delete(`/catalog/study/${id}`, {
        headers: {
          Authorization: `Bearer ${authStore.accessToken}`,
        },
      }));
  }

  async function loadStudy(id: string) {
    study.value = undefined;
    return api.get(`/catalog/study/${id}`).then((response) => {
      study.value = response.data;
      return Promise.all([loadStudyBuildings(), loadStudySpaces(), loadStudyInstruments(), loadStudyDatasets()]);
    });
  }

  async function loadStudyBuildings() {
    buildings.value = [];
    return api
      .get(`/catalog/study/${study.value?.id}/buildings`)
      .then((response) => {
        buildings.value = response.data?.data || [];
      });
  }

  async function loadStudySpaces() {
    spaces.value = [];
    return api
      .get(`/catalog/study/${study.value?.id}/spaces`)
      .then((response) => {
        spaces.value = response.data?.data || [];
      });
  }

  async function loadStudyInstruments() {
    instruments.value = [];
    return api
      .get(`/catalog/study/${study.value?.id}/instruments`)
      .then((response) => {
        instruments.value = response.data?.data || [];
      });
  }

  async function loadStudyDatasets() {
    datasets.value = [];
    return api
      .get(`/catalog/study/${study.value?.id}/datasets`)
      .then((response) => {
        datasets.value = response.data?.data || [];
      });
  }

  return {
    loadStudySummaries,
    deleteStudy,
    loadStudies,
    loadBuildings,
    loadSpaces,
    loadStudy,
    study,
    buildings,
    spaces,
    instruments,
    datasets,
    showStudyDetails,
  };
});
