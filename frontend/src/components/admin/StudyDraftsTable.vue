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
      @row-dblclick="onRowDblClick"
    >
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

function onRowDblClick(evt, row: Study) {
  contrib.load(row.identifier).then(() => {
    showDialog.value = true;
  });
}

function onSave() {
  showUpload.value = true;
}

function onUploadClose() {
  fetchStudyDrafts();
}
</script>