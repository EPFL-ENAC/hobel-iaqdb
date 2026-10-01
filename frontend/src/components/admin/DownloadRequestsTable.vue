<template>
  <q-table
    flat
    :rows="rows"
    :columns="columns"
    v-model:pagination="pagination"
    :rows-per-page-options="[10, 25, 50, 100]"
    :loading="loading"
    row-key="id"
    @request="onRequest"
  >
    <template v-slot:top-right>
      <q-btn flat dense round icon="refresh" color="grey-8" @click="onRequest({ pagination })" />
    </template>
    <template v-slot:body-cell-status="props">
      <q-td :props="props">
        <q-badge :color="STATUS_COLORS[props.value as DownloadRequest['status']]" :label="props.value" />
        <q-icon v-if="props.row.error" name="error_outline" color="negative" class="q-ml-xs">
          <q-tooltip>{{ props.row.error }}</q-tooltip>
        </q-icon>
      </q-td>
    </template>
    <template v-slot:body-cell-title="props">
      <q-td :props="props">
        <div class="text-bold">{{ props.row.title }}</div>
        <div class="text-caption text-grey-8 ellipsis-2-lines" style="max-width: 400px; white-space: normal">
          {{ props.row.description }}
        </div>
      </q-td>
    </template>
    <template v-slot:body-cell-email="props">
      <q-td :props="props">
        <a :href="`mailto:${props.value}`" class="epfl">{{ props.value }}</a>
      </q-td>
    </template>
    <template v-slot:body-cell-selection="props">
      <q-td :props="props">
        <div v-if="props.row.query.parameters?.length">{{ props.row.query.parameters.join(', ') }}</div>
        <div v-if="props.row.query.from || props.row.query.to" class="text-caption">
          {{ props.row.query.from || '…' }} → {{ props.row.query.to || '…' }}
        </div>
        <q-icon v-if="props.row.query.filter" name="filter_alt" color="grey-8">
          <q-tooltip>{{ props.row.query.filter }}</q-tooltip>
        </q-icon>
      </q-td>
    </template>
  </q-table>
</template>

<script setup lang="ts">
import type { DownloadRequest } from '@/models';
import { list } from '@/api/download';
import { notifyError } from '@/utils/notify';
import { toDatetimeString } from '@/utils/time';

interface Pagination {
  page: number;
  rowsPerPage: number;
  rowsNumber?: number;
}

const STATUS_COLORS: Record<DownloadRequest['status'], string> = {
  pending: 'grey-7',
  running: 'info',
  ready: 'positive',
  failed: 'negative',
  expired: 'grey-5',
};

const authStore = useAuthStore();

const loading = ref(false);
const rows = ref<DownloadRequest[]>([]);
const pagination = ref<Pagination>({ page: 1, rowsPerPage: 25, rowsNumber: 0 });

function formatSize(bytes?: number) {
  return bytes === undefined || bytes === null ? '-' : `${(bytes / (1 << 20)).toFixed(1)} MB`;
}

const columns = [
  { name: 'created_at', label: 'Requested', align: 'left' as const, field: 'created_at', format: toDatetimeString },
  { name: 'status', label: 'Status', align: 'left' as const, field: 'status' },
  { name: 'title', label: 'Title', align: 'left' as const, field: 'title' },
  { name: 'email', label: 'Email', align: 'left' as const, field: 'email' },
  { name: 'selection', label: 'Selection', align: 'left' as const, field: 'query' },
  {
    name: 'n_records',
    label: 'Records',
    align: 'right' as const,
    field: 'n_records',
    format: (v: number) => v.toLocaleString(),
  },
  { name: 'size', label: 'Size', align: 'right' as const, field: 'size', format: formatSize },
  { name: 'notified_at', label: 'Notified', align: 'left' as const, field: 'notified_at', format: toDatetimeString },
  { name: 'expires_at', label: 'Expires', align: 'left' as const, field: 'expires_at', format: toDatetimeString },
  { name: 'client_ip', label: 'Client IP', align: 'left' as const, field: 'client_ip' },
];

function onRequest(props: { pagination: Pagination }) {
  const { page, rowsPerPage } = props.pagination;
  loading.value = true;
  list((page - 1) * rowsPerPage, rowsPerPage)
    .then((result) => {
      rows.value = result.data;
      pagination.value = { page, rowsPerPage, rowsNumber: result.total };
    })
    .catch(notifyError)
    .finally(() => (loading.value = false));
}

onMounted(() => {
  if (authStore.isAuthenticated) onRequest({ pagination: pagination.value });
});

watch(
  () => authStore.isAuthenticated,
  (authenticated) => {
    if (authenticated) onRequest({ pagination: pagination.value });
    else rows.value = [];
  },
);
</script>
