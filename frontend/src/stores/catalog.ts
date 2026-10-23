import { defineStore } from 'pinia';
import { api } from '@/boot/api';
import type {
  Dataset,
  Study,
  StudiesResult,
  BuildingsResult,
  SpacesResult,
  StudySummariesResult,
} from '@/models';
import { buildingCriteria, spaceCriteria, studyCriteria } from '@/api/explore';

export const useCatalogStore = defineStore('catalog', () => {
  const authStore = useAuthStore();

  const study = ref<Study>();
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

  /** The datasets with these ids, whatever the filters. */
  async function loadDatasetsByIds(ids: number[]): Promise<Dataset[]> {
    if (!ids.length) return [];
    return api
      .get('/catalog/datasets', {
        params: {
          filter: JSON.stringify({ id: ids }),
          range: JSON.stringify([0, ids.length - 1]),
        },
      })
      .then((response) => (response.data as { data: Dataset[] }).data);
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
      ...studyCriteria(),
      $building: buildingCriteria(),
      $space: spaceCriteria(),
    };
  }

  function getBuildingFilter() {
    return {
      ...buildingCriteria(),
      $study: studyCriteria(),
      $space: spaceCriteria(),
    };
  }

  function getSpaceFilter() {
    return {
      ...spaceCriteria(),
      $study: studyCriteria(),
      $building: buildingCriteria(),
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
    });
  }

  async function loadStudyItems<T>(
    items: 'buildings' | 'spaces' | 'instruments' | 'datasets',
    skip: number,
    limit: number,
    sortBy?: string,
    descending = false,
  ): Promise<{ total: number; data: T[] }> {
    return api
      .get(`/catalog/study/${study.value?.id}/${items}`, {
        params: {
          range: JSON.stringify([skip, limit + skip - 1]),
          sort: sortBy ? JSON.stringify([sortBy, descending ? 'DESC' : 'ASC']) : undefined,
        },
      })
      .then((response) => response.data);
  }

  return {
    loadStudySummaries,
    loadDatasetsByIds,
    deleteStudy,
    loadStudies,
    loadBuildings,
    loadSpaces,
    loadStudy,
    loadStudyItems,
    study,
    showStudyDetails,
  };
});
