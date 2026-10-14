<template>
  <div>
    <q-table
      ref="tableRef"
      flat
      :rows="rows"
      :columns="columns"
      v-model:pagination="pagination"
      :rows-per-page-options="[10, 25, 50, 100]"
      :loading="loading"
      :row-key="(row: StudyBundle) => row.study.identifier"
      @request="onRequest"
    >
      <template v-slot:top-left>
        <div class="row items-center q-gutter-sm">
          <q-btn
            v-for="value in ['all', 'published', 'not_published'] as const"
            :key="value"
            :label="t(`admin.${value}`)"
            no-caps
            rounded
            unelevated
            size="sm"
            :color="publishedFilter === value ? 'secondary' : 'grey-3'"
            :text-color="publishedFilter === value ? 'white' : 'grey-8'"
            @click="publishedFilter = value"
          />
          <q-input
            v-model="text"
            :placeholder="t('admin.contributions_search')"
            debounce="300"
            clearable
            dense
            outlined
            style="min-width: 300px"
          >
            <template v-slot:prepend>
              <q-icon name="search" />
            </template>
          </q-input>
        </div>
      </template>
      <template v-slot:top-right>
        <q-btn flat dense round icon="refresh" color="grey-8" @click="fetchStudyBundles()" />
      </template>
      <template v-slot:body-cell-identifier="props">
        <q-td :props="props">
          <q-badge class="q-pa-xs" color="secondary">{{ props.value }}</q-badge>
          <div class="float-right">
            <q-btn
              rounded
              dense
              flat
              size="sm"
              color="grey-8"
              :title="t('approve')"
              icon="publish"
              class="q-ml-xs"
              @click="onShowApprove(props.row)"
            />
            <q-btn
              rounded
              dense
              flat
              size="sm"
              color="grey-8"
              :title="t('edit')"
              icon="edit"
              class="q-ml-xs"
              @click="onShowEdit(props.row)"
            />
            <q-btn
              rounded
              dense
              flat
              size="sm"
              color="grey-8"
              :title="t('delete')"
              icon="delete"
              class="q-ml-xs"
              @click="onShowDelete(props.row)"
            />
          </div>
        </q-td>
      </template>
      <template v-slot:body-cell-contributors="props">
        <q-td :props="props">
          <div v-for="contributor in props.value" :key="contributor.email">
            <span>{{ contributor.name }}</span> &lt;<a :mailto="contributor.email" class="epfl">{{ contributor.email }}</a>&gt;
          </div>
        </q-td>
      </template>
    </q-table>
    <study-draft-dialog v-model="showDialog" @save="onSave"/>
    <study-upload-dialog v-model="showUpload" @close="onUploadClose"/>
    <confirm-dialog v-model="showDelete" :text="t('confirm_study_draft_delete', { identifier: selected?.study.name })" @confirm="onDelete"/>
    <confirm-dialog v-model="showApprove" :text="t('confirm_study_draft_approval', { identifier: selected?.study.name })" @confirm="onApprove"/>
  </div>
</template>

<script setup lang="ts">
import type { StudyBundle, Study, Contribution } from '@/models';
import StudyDraftDialog from '@/components/admin/StudyDraftDialog.vue';
import StudyUploadDialog from '@/components/contribute/StudyUploadDialog.vue';
import ConfirmDialog from '@/components/ConfirmDialog.vue';
import { notifyError, notifySuccess } from '@/utils/notify';
import { toDatetimeString } from '@/utils/time';
import { dataEmbargoOptions } from '@/utils/options';

const { t } = useI18n();
const authStore = useAuthStore();
const contrib = useContributeStore();

interface Pagination {
  sortBy: string | null;
  descending: boolean;
  page: number;
  rowsPerPage: number;
  rowsNumber?: number;
}

const tableRef = ref();
const loading = ref(true);
const rows = ref<StudyBundle[]>([]);
const pagination = ref<Pagination>({
  sortBy: 'identifier',
  descending: false,
  page: 1,
  rowsPerPage: 25,
  rowsNumber: 0,
});
const text = ref<string | null>(null);
const showDialog = ref(false);
const showUpload = ref(false);
const showDelete = ref(false);
const showApprove = ref(false);
const selected = ref<StudyBundle>();

onMounted(() => {
  void fetchStudyBundles();
});

watch(() => authStore.isAuthenticated, () => {
  if (authStore.isAuthenticated) {
    void fetchStudyBundles();
  } else {
    rows.value = [];
  }
});

const publishedFilter = ref<'all' | 'published' | 'not_published'>('all');

watch([publishedFilter, text], () => onRequest({ pagination: { ...pagination.value, page: 1 } }));

const columns = computed(() => [
  {
    name: 'identifier',
    label: 'Identifier',
    align: 'left' as const,
    field: 'study',
    format: (v: Study) => v.identifier,
    style: 'width: 360px',
    sortable: true,
  },
  {
    name: 'name',
    label: 'Name',
    align: 'left' as const,
    field: 'study',
    format: (v: Study) => v.name,
    sortable: true,
  },
  {
    name: 'contributors',
    label: 'Contributors',
    align: 'left' as const,
    field: 'study',
    format: (v: Study) => v.contributors,
  },
  {
    name: 'buildings',
    label: 'Buildings',
    align: 'left' as const,
    field: 'study',
    format: (v: Study) => v.buildings?.length,
  },
  {
    name: 'instruments',
    label: 'Instruments',
    align: 'left' as const,
    field: 'study',
    format: (v: Study) => v.instruments?.length,
  },
  {
    name: 'datasets',
    label: 'Datasets',
    align: 'left' as const,
    field: 'study',
    format: (v: Study) => v.datasets?.length,
  },
  {
    name: 'data_embargo',
    label: 'Data Embargo',
    align: 'left' as const,
    field: 'contribution',
    format: (v: Contribution) => getDataEmbargoLabel(v?.data_embargo),
    sortable: true,
  },
  {
    name: 'created_at',
    label: 'Created At',
    align: 'left' as const,
    field: 'contribution',
    format: (v: Contribution) => toDatetimeString(v?.created_at),
    sortable: true,
  },
  {
    name: 'updated_at',
    label: 'Updated At',
    align: 'left' as const,
    field: 'contribution',
    format: (v: Contribution) => toDatetimeString(v?.updated_at),
    sortable: true,
  },
  {
    name: 'published_at',
    label: 'Published At',
    align: 'left' as const,
    field: 'contribution',
    format: (v: Contribution) => toDatetimeString(v?.published_at),
    sortable: true,
  },
]);

function getDataEmbargoLabel(dataEmbargo: string | null | undefined): string {
  return dataEmbargo ? dataEmbargoOptions.find(option => option.value === dataEmbargo)?.label || dataEmbargo : '-';
}

let requestId = 0;

function onRequest(props: { pagination: Pagination }) {
  if (!authStore.isAuthenticated || !authStore.isAdmin) {
    return Promise.resolve();
  }
  const { page, rowsPerPage, sortBy, descending } = props.pagination;
  const id = ++requestId;
  loading.value = true;
  return contrib.getBundles({
    ...(text.value ? { q: text.value } : {}),
    ...(publishedFilter.value !== 'all' ? { published: publishedFilter.value === 'published' } : {}),
    ...(sortBy ? { sort: sortBy, desc: descending } : {}),
    skip: (page - 1) * rowsPerPage,
    limit: rowsPerPage,
  })
    .then((result) => {
      // a newer request was sent meanwhile: drop this stale response
      if (id !== requestId) return;
      rows.value = result.data;
      pagination.value = { page, rowsPerPage, sortBy, descending, rowsNumber: result.total };
    })
    .catch(notifyError)
    .finally(() => {
      if (id === requestId) loading.value = false;
    });
}

function fetchStudyBundles() {
  return onRequest({ pagination: pagination.value });
}

function onShowEdit(row: StudyBundle) {
  void contrib.load(row.study.identifier).then(() => {
    showDialog.value = true;
  });
}

function onShowApprove(row: StudyBundle) {
  selected.value = row;
  showApprove.value = true;
}

function onApprove() {
  if (selected.value) {
    contrib.publishDraft(selected.value.study).then(() => {
      void fetchStudyBundles();
    })
    .then(() => {
      notifySuccess('study_draft_approval_success');
    })
    .catch(notifyError)
    .finally(() => {
      showApprove.value = false;
      selected.value = undefined;
    });
  }
}

function onShowDelete(row: StudyBundle) {
  selected.value = row;
  showDelete.value = true;
}

function onDelete() {
  if (selected.value) {
    void contrib.deleteDraft(selected.value.study).then(() => {
      void fetchStudyBundles();
    });
  }
}

function onSave() {
  showUpload.value = true;
}

function onUploadClose() {
  void fetchStudyBundles();
}
</script>
