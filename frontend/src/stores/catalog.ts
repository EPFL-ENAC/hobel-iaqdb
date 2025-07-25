import { defineStore } from 'pinia';
import { api } from 'src/boot/api';
import type {
  Study,
  Building,
  Space,
  Instrument,
  Dataset,
  StudiesResult,
  BuildingsResult,
  SpacesResult,
  StudySummariesResult,
  GroupByResult,
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
    filtered = true
  ): Promise<StudySummariesResult> {
    return api
      .get('/catalog/study-summaries', {
        params: {
          range: JSON.stringify([skip, limit + skip - 1]),
          filter: filtered ? JSON.stringify(getStudyFilter()) : undefined,
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
          filter: JSON.stringify(getStudyFilter()),
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
          filter: JSON.stringify(getBuildingFilter()),
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
          filter: JSON.stringify(getSpaceFilter()),
        },
        paramsSerializer: {
          indexes: null, // no brackets at all
        },
      })
      .then((response) => response.data);
  }

  function getStudyFilter() {
    return {
      ...getStudyCriteria(),
      $building: getBuildingCriteria(),
      $space: getSpaceCriteria(),
    };
  }
  
  function getBuildingFilter() {
    return {
      ...getBuildingCriteria(),
      $study: getStudyCriteria(),
      $space: getSpaceCriteria(),
    };
  }

  function getSpaceFilter() {
    return {
      ...getSpaceCriteria(),
      $study: getStudyCriteria(),
      $building: getBuildingCriteria(),
    };
  }

  function getStudyCriteria() {
    return {
      identifier: filterStore.study_ids && filterStore.study_ids.length
        ? filterStore.study_ids
        : undefined
    };
  }

  function getBuildingCriteria() {
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
    // strip out the country code
    const cities = filterStore.cities ? filterStore.cities.map((city: string) => (city.substring(0, city.length - 4))) : [];
    return {
      $and: construction_years.length || altitudes.length ? [
        ...construction_years,
        ...altitudes,
      ] : undefined,
      type:
        filterStore.building_types && filterStore.building_types.length
          ? filterStore.building_types
          : undefined,
      country:
        filterStore.countries && filterStore.countries.length
          ? filterStore.countries
          : undefined,
      city:
        cities && cities.length
          ? cities
          : undefined,
      socioeconomic_status:
        filterStore.socioeconomic_status && filterStore.socioeconomic_status.length
          ? filterStore.socioeconomic_status
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
    };
  }

  function getSpaceCriteria() {
    return {
      mechanical_ventilation_type:
        filterStore.mechanical_ventilation_types && filterStore.mechanical_ventilation_types.length
          ? filterStore.mechanical_ventilation_types
          : undefined,
    };
  }

  async function deleteStudy(id: string) {
    if (!authStore.isAuthenticated) return Promise.reject(new Error('Not authenticated'));
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

  async function countStudies(
    by: string,
    filtered = true
  ): Promise<GroupByResult> {
    return api
      .get('/stats/frequencies/studies', {
        params: {
          by,
          filter: filtered ? JSON.stringify(getStudyFilter()) : undefined,
        },
        paramsSerializer: {
          indexes: null, // no brackets at all
        },
      })
      .then((response) => response.data);
  }
  
  async function countBuildings(
    by: string,
    filtered = true
  ): Promise<GroupByResult> {
    return api
      .get('/stats/frequencies/buildings', {
        params: {
          by,
          filter: filtered ? JSON.stringify(getBuildingFilter()) : undefined,
        },
        paramsSerializer: {
          indexes: null, // no brackets at all
        },
      })
      .then((response) => response.data);
  }
  
  async function countSpaces(
    by: string,
    filtered = true
  ): Promise<GroupByResult> {
    return api
      .get('/stats/frequencies/spaces', {
        params: {
          by,
          filter: filtered ? JSON.stringify(getSpaceFilter()) : undefined,
        },
        paramsSerializer: {
          indexes: null, // no brackets at all
        },
      })
      .then((response) => response.data);
  }

  return {
    loadStudySummaries,
    deleteStudy,
    loadStudies,
    loadBuildings,
    loadSpaces,
    loadStudy,
    countStudies,
    countBuildings,
    countSpaces,
    study,
    buildings,
    spaces,
    instruments,
    datasets,
    showStudyDetails,
  };
});
