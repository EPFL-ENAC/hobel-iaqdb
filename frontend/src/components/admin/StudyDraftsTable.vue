<template>
  <div>
    <q-table
      ref="tableRef"
      flat
      :rows="rows"
      :columns="columns"
      v-model:pagination="pagination"
      :loading="loading"
      row-key="identifier"
    >
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
import type { StudyBundle, Study, Contribution } from 'src/models';
import StudyDraftDialog from 'src/components/admin/StudyDraftDialog.vue';
import StudyUploadDialog from 'src/components/contribute/StudyUploadDialog.vue';
import ConfirmDialog from 'src/components/ConfirmDialog.vue';
import { notifyError, notifySuccess } from 'src/utils/notify';
import { toDatetimeString } from 'src/utils/time';
import { dataEmbargoOptions } from 'src/utils/options';

const { t } = useI18n();
const authStore = useAuthStore();
const contrib = useContributeStore();

const tableRef = ref();
const loading = ref(true);
const studyBundles = ref<StudyBundle[]>([]);
  const pagination = ref({
  sortBy: 'identifier',
  descending: false,
  page: 1,
  rowsPerPage: 25,
});
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
    studyBundles.value = [];
  }
});

const rows = computed(() => studyBundles.value || []);

const columns = computed(() => [
  { name: 'identifier', label: 'Identifier', align: 'left' as const, field: 'study', format: (v: Study) => v.identifier,
    style: 'width: 360px', },
  { name: 'name', label: 'Name', align: 'left' as const, field: 'study',  format: (v: Study) => v.name },
  { name: 'contributors', label: 'Contributors', align: 'left' as const, field: 'study', format: (v: Study) => v.contributors },
  { name: 'buildings', label: 'Buildings', align: 'left' as const, field: 'study', format: (v: Study) => v.buildings?.length },
  { name: 'instruments', label: 'Instruments', align: 'left' as const, field: 'study', format: (v: Study) => v.instruments?.length },
  { name: 'datasets', label: 'Datasets', align: 'left' as const, field: 'study', format: (v: Study) => v.datasets?.length },
  { name: 'data_embargo', label: 'Data Embargo', align: 'left' as const, field: 'contribution', format: (v: Contribution) => getDataEmbargoLabel(v?.data_embargo) },
  { name: 'created_at', label: 'Created At', align: 'left' as const, field: 'contribution', format: (v: Contribution) => toDatetimeString(v?.created_at) },
  { name: 'updated_at', label: 'Updated At', align: 'left' as const, field: 'contribution', format: (v: Contribution) => toDatetimeString(v?.updated_at) },
  { name: 'published_at', label: 'Published At', align: 'left' as const, field: 'contribution', format: (v: Contribution) => toDatetimeString(v?.published_at) },
]);

function getDataEmbargoLabel(dataEmbargo: string | null | undefined): string {
  return dataEmbargo ? dataEmbargoOptions.find(option => option.value === dataEmbargo)?.label || dataEmbargo : '-';
}

async function fetchStudyBundles() {
  if (!authStore.isAuthenticated || !authStore.isAdmin) {
    return Promise.resolve();
  }
  loading.value = true;
  // fetch study drafts in bundles
  return contrib.getBundles().then((bundles) => {
    studyBundles.value = bundles.data;
  }).finally(() => {
    loading.value = false;
  });
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
