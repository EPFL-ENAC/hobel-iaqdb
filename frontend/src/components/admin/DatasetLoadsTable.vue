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
    <template v-slot:top-left>
      <div class="row items-center q-gutter-sm">
        <q-btn
          v-for="value in ['all', 'pending', 'ready', 'failed'] as const"
          :key="value"
          :label="t(`admin.${value}`)"
          no-caps
          rounded
          unelevated
          size="sm"
          :color="status === value ? 'secondary' : 'grey-3'"
          :text-color="status === value ? 'white' : 'grey-8'"
          @click="status = value"
        />
        <q-select
          v-model="studyId"
          :options="studyOptions"
          :label="t('study.label')"
          emit-value
          map-options
          clearable
          dense
          outlined
          style="min-width: 240px"
        />
        <q-input
          v-model="text"
          :placeholder="t('admin.loads_search')"
          debounce="300"
          clearable
          dense
          outlined
          style="min-width: 240px"
        >
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
        </q-input>
      </div>
    </template>
    <template v-slot:top-right>
      <q-btn flat dense round icon="refresh" color="grey-8" @click="onRequest({ pagination })" />
    </template>
    <template v-slot:body-cell-study="props">
      <q-td :props="props">
        <q-badge class="q-pa-xs" color="secondary">{{ props.row.study_identifier }}</q-badge>
        <div class="text-caption text-grey-8">{{ props.row.study_name }}</div>
      </q-td>
    </template>
    <template v-slot:body-cell-summary_status="props">
      <q-td :props="props">
        <q-badge :color="STATUS_COLORS[props.value as LoadStatus]" :label="props.value" />
      </q-td>
    </template>
    <template v-slot:body-cell-summary_error="props">
      <q-td :props="props">
        <div v-if="props.value" class="text-negative ellipsis-2-lines" style="max-width: 400px; white-space: normal">
          {{ props.value }}
          <q-tooltip max-width="600px">{{ props.value }}</q-tooltip>
        </div>
      </q-td>
    </template>
    <template v-slot:body-cell-report="props">
      <q-td :props="props">
        <q-btn v-if="props.row.load_report" flat dense round size="sm" icon="info_outline" color="grey-8">
          <q-popup-proxy>
            <q-markup-table dense flat bordered>
              <tbody>
                <tr v-for="[key, value] in reportEntries(props.row.load_report)" :key="key">
                  <td>{{ key }}</td>
                  <td class="text-right">{{ value }}</td>
                </tr>
              </tbody>
            </q-markup-table>
          </q-popup-proxy>
        </q-btn>
      </q-td>
    </template>
  </q-table>
</template>

<script setup lang="ts">
import type { DatasetLoad, LoadReport, LoadStatus } from '@/models';
import { listLoads } from '@/api/datasets';
import { notifyError } from '@/utils/notify';
import { toDatetimeString } from '@/utils/time';

interface Pagination {
  page: number;
  rowsPerPage: number;
  rowsNumber?: number;
}

const STATUS_COLORS: Record<LoadStatus, string> = {
  pending: 'grey-7',
  ready: 'positive',
  failed: 'negative',
};

const { t } = useI18n();
const authStore = useAuthStore();
const catalogStore = useCatalogStore();

const loading = ref(false);
const rows = ref<DatasetLoad[]>([]);
const pagination = ref<Pagination>({ page: 1, rowsPerPage: 25, rowsNumber: 0 });
const status = ref<'all' | LoadStatus>('all');
const studyId = ref<number | null>(null);
const text = ref<string | null>(null);
const studyOptions = ref<{ label: string; value: number }[]>([]);

function rejected(report?: LoadReport) {
  if (!report) return undefined;
  const sum = (counts: Record<string, number>) => Object.values(counts).reduce((a, b) => a + b, 0);
  return (
    sum(report.unknown_parameter) +
    sum(report.unknown_unit) +
    sum(report.unparseable_value) +
    report.unparseable_timestamp
  );
}

/** Flat key/value lines, the per-parameter counts as `key: parameter`. */
function reportEntries(report: LoadReport): [string, number][] {
  return Object.entries(report).flatMap(([key, value]) =>
    typeof value === 'number'
      ? [[key, value] as [string, number]]
      : Object.entries(value as Record<string, number>).map(([sub, n]) => [`${key}: ${sub}`, n] as [string, number]),
  );
}

const formatCount = (v?: number) => (v === undefined ? '-' : v.toLocaleString());

function duration(row: DatasetLoad) {
  if (!row.load_started_at || !row.load_finished_at) return undefined;
  return (new Date(row.load_finished_at).getTime() - new Date(row.load_started_at).getTime()) / 1000;
}

const columns = [
  {
    name: 'study',
    label: 'Study',
    align: 'left' as const,
    field: 'study_identifier',
    style: 'max-width: 400px; white-space: normal',
  },
  { name: 'name', label: 'Dataset', align: 'left' as const, field: 'name' },
  { name: 'summary_status', label: 'Status', align: 'left' as const, field: 'summary_status' },
  { name: 'summary_error', label: 'Error', align: 'left' as const, field: 'summary_error' },
  {
    name: 'loaded',
    label: 'Loaded',
    align: 'right' as const,
    field: (row: DatasetLoad) => row.load_report?.loaded,
    format: formatCount,
  },
  {
    name: 'rejected',
    label: 'Rejected',
    align: 'right' as const,
    field: (row: DatasetLoad) => rejected(row.load_report),
    format: formatCount,
  },
  {
    name: 'load_started_at',
    label: 'Started',
    align: 'left' as const,
    field: 'load_started_at',
    format: toDatetimeString,
  },
  {
    name: 'duration',
    label: 'Duration',
    align: 'right' as const,
    field: duration,
    format: (v?: number) => (v === undefined ? '-' : `${v.toFixed(1)} s`),
  },
  { name: 'report', label: 'Report', align: 'center' as const, field: 'load_report' },
];

function onRequest(props: { pagination: Pagination }) {
  const { page, rowsPerPage } = props.pagination;
  loading.value = true;
  listLoads({
    ...(status.value !== 'all' ? { status: status.value } : {}),
    ...(studyId.value !== null ? { study_id: studyId.value } : {}),
    ...(text.value ? { q: text.value } : {}),
    skip: (page - 1) * rowsPerPage,
    limit: rowsPerPage,
  })
    .then((result) => {
      rows.value = result.data;
      pagination.value = { page, rowsPerPage, rowsNumber: result.total };
    })
    .catch(notifyError)
    .finally(() => (loading.value = false));
}

function loadStudyOptions() {
  // ponytail: first 1000 studies only, page the select if the catalog ever grows past it
  catalogStore
    .loadStudySummaries(0, 1000, false)
    .then((result) => {
      studyOptions.value = result.data.map((s) => ({ label: `${s.identifier} - ${s.name}`, value: Number(s.id) }));
    })
    .catch(notifyError);
}

function init() {
  onRequest({ pagination: pagination.value });
  loadStudyOptions();
}

watch([status, studyId, text], () => onRequest({ pagination: { ...pagination.value, page: 1 } }));

onMounted(() => {
  if (authStore.isAuthenticated) init();
});

watch(
  () => authStore.isAuthenticated,
  (authenticated) => {
    if (authenticated) init();
    else rows.value = [];
  },
);
</script>
