<template>
  <div>
    <q-table
      ref="tableRef"
      flat
      grid
      :rows="rows"
      row-key="id"
      v-model:pagination="pagination"
      :loading="loading"
      @request="onRequest"
    >
      <template v-slot:item="props">
        <div class="col-3">
          <q-card flat bordered @click="onRowClick(props.row)" class="cursor-pointer q-ma-md">
            <q-card-section>
              <div class="text-h6">{{ props.row.name }}</div>
              <div class="text-subtitle2 text-grey-8 q-mb-md">
                {{ truncateText(props.row.description, 300) }}
              </div>
              <div>
                <q-chip
                  color="secondary"
                  class="text-white on-left"
                  :label="$t('buildings_with_count', getBuildingsCount(props.row))"
                />
                <q-chip
                  color="secondary"
                  class="text-white on-left"
                  :label="$t('datasets_with_count', getDatasetsCount(props.row))"
                />
                <q-chip
                  :label="
                    $t('from_to', {
                      from: props.row.start_year,
                      to: props.row.end_year,
                    })
                  "
                />
              </div>
            </q-card-section>
          </q-card>
        </div>
      </template>
    </q-table>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyList',
});
</script>
<script setup lang="ts">
import { Study, StudiesResult } from 'src/models';

const catalogStore = useCatalogStore();
const filtersStore = useFiltersStore();
const router = useRouter();

const tableRef = ref();
const rows = ref<Study[]>([]);
const pagination = ref({
  sortBy: 'id',
  descending: false,
  page: 1,
  rowsPerPage: 25,
});
const loading = ref(false);

onMounted(updateTable);

watch(() => filtersStore.updates, updateTable);

function getBuildingsCount(study: Study) {
  return study.buildings?.length || 0;
}

function getDatasetsCount(study: Study) {
  return study.datasets?.length || 0;
}

function updateTable() {
  tableRef.value.requestServerInteraction();
}

function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

function onRequest(props) {
  const { page, rowsPerPage, sortBy, descending } = props.pagination;

  const skip = (page - 1) * rowsPerPage;
  const limit = rowsPerPage;
  loading.value = true;

  catalogStore.loadStudies(skip, limit).then((result: StudiesResult) => {
    rows.value = result.data;
    pagination.value.rowsNumber = result.total;

    // don't forget to update local pagination object
    pagination.value.page = page;
    pagination.value.rowsPerPage = rowsPerPage;
    pagination.value.sortBy = sortBy;
    pagination.value.descending = descending;

    // ...and turn of loading indicator
    loading.value = false;
  });
}

function onRowClick(val: Study) {
  router.push(`/study?id=${val.identifier}`);
}
</script>
