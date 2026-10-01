/**
 * Measurement load state of the published datasets (admin).
 */
import { api } from '@/boot/api';
import type { DatasetLoadsResult, LoadStatus } from '@/models';
import { useAuthStore } from '@/stores/auth';

export interface DatasetLoadsQuery {
  status?: LoadStatus;
  study_id?: number;
  q?: string;
  skip: number;
  limit: number;
}

export async function listLoads(query: DatasetLoadsQuery): Promise<DatasetLoadsResult> {
  const authStore = useAuthStore();
  await authStore.updateToken();
  return api
    .get('/contribute/dataset-loads', {
      params: query,
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    .then((response) => response.data as DatasetLoadsResult);
}
