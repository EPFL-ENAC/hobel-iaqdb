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
          <q-badge class="q-pa-xs" color="secondary" :title="props.value">{{ props.value.split('-')[0] }}...</q-badge>
          <div class="float-right">
            <q-btn
              rounded
              dense
              flat
              size="sm"
              color="grey-8"
              :title="$t('edit')"
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
              :title="$t('delete')"
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
    <confirm-dialog v-model="showDelete" :text="$t('confirm_study_draft_delete', { identifier: selected?.identifier })" @confirm="onDelete"/>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyDraftsTable',
});
</script>
<script setup lang="ts">  
import { Study, Building, Instrument, Dataset } from 'src/models';
import StudyDraftDialog from 'src/components/admin/StudyDraftDialog.vue';
import StudyUploadDialog from 'src/components/contribute/StudyUploadDialog.vue';
import ConfirmDialog from 'src/components/ConfirmDialog.vue';

const authStore = useAuthStore();
const contrib = useContributeStore();

const tableRef = ref();
const loading = ref(true);
const studyDrafts = ref<Study[]>([]);
  const pagination = ref({
  sortBy: 'identifier',
  descending: false,
  page: 1,
  rowsPerPage: 5,
});
const showDialog = ref(false);
const showUpload = ref(false);
const showDelete = ref(false);
const selected = ref<Study | null>(null);

onMounted(() => {
  fetchStudyDrafts();
});

watch(() => authStore.isAuthenticated, () => {
  if (authStore.isAuthenticated) {
    fetchStudyDrafts();
  } else {
    studyDrafts.value = [];
  }
});

const rows = computed(() => studyDrafts.value || []);

const columns = computed(() => [
  { name: 'identifier', label: 'Identifier', align: 'left', field: 'identifier' },
  { name: 'name', label: 'Name', align: 'left', field: 'name' },
  { name: 'contributors', label: 'Contributors', align: 'left', field: 'contributors' },
  { name: 'buildings', label: 'Buildings', align: 'left', field: 'buildings', format: (v: Building[]) => v.length },
  { name: 'instruments', label: 'Instruments', align: 'left', field: 'instruments', format: (v: Instrument[]) => v.length },
  { name: 'datasets', label: 'Datasets', align: 'left', field: 'datasets', format: (v: Dataset[]) => v.length },
]);

async function fetchStudyDrafts() {
  if (!authStore.isAuthenticated || !authStore.isAdmin) {
    return Promise.resolve();
  }
  loading.value = true;
  // fetch study drafts
  return contrib.getDrafts().then((drafts) => {
    studyDrafts.value = drafts.data;
  }).finally(() => {
    loading.value = false;
  });
}

function onShowEdit(row: Study) {
  contrib.load(row.identifier).then(() => {
    showDialog.value = true;
  });
}

function onShowDelete(row: Study) {
  selected.value = row;
  showDelete.value = true;
}

function onDelete() {
  if (selected.value) {
    contrib.deleteDraft(selected.value).then(() => {
      fetchStudyDrafts();
    });
  }
}

function onSave() {
  showUpload.value = true;
}

function onUploadClose() {
  fetchStudyDrafts();
}
</script>