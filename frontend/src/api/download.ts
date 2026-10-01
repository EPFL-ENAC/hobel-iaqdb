/**
 * Download of the raw measurements matching the Explore filters: estimate,
 * then request; the link is emailed when the archive is ready.
 */
import { api } from '@/boot/api';
import type { DownloadEstimate, DownloadForm, DownloadRequestsResult, DownloadSelection } from '@/models';
import { canonicalParams, exploreFilter, exploreRange } from '@/api/explore';
import { useExploreStore } from '@/stores/explore';
import { useAuthStore } from '@/stores/auth';

/** The current Explore selection, as the charts send it. */
export function downloadSelection(): DownloadSelection {
  const { filter, parameters } = canonicalParams({
    filter: exploreFilter(),
    parameters: useExploreStore().parameters,
  });
  return {
    ...(filter ? { filter } : {}),
    parameters: parameters ? parameters.split(',') : [],
    ...exploreRange(),
  };
}

export async function estimate(selection: DownloadSelection): Promise<DownloadEstimate> {
  return api.post('/downloads/estimate', selection).then((response) => response.data as DownloadEstimate);
}

export async function request(form: DownloadForm): Promise<{ id: number; status: string; n_records: number }> {
  return api.post('/downloads', form).then((response) => response.data);
}

/** Download requests, most recent first (admin). */
export async function list(skip: number, limit: number): Promise<DownloadRequestsResult> {
  const authStore = useAuthStore();
  await authStore.updateToken();
  return api
    .get('/downloads', {
      params: { skip, limit },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    .then((response) => response.data as DownloadRequestsResult);
}
