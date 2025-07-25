<template>
  <div>
    <q-table
      ref="tableRef"
      flat
      :rows="rows"
      row-key="id"
      v-model:pagination="pagination"
      :loading="loading"
      @request="onRequest"
    ></q-table>
  </div>
</template>

<script setup lang="ts">
import type { Space, SpacesResult } from 'src/models';
import type { TableRequestProps } from 'src/components/models';

const catalogStore = useCatalogStore();
const filtersStore = useFiltersStore();

const tableRef = ref();
const rows = ref<Space[]>([]);
const pagination = ref({
  sortBy: 'id',
  descending: false,
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0,
});
const loading = ref(false);

onMounted(updateTable);

watch(() => filtersStore.updates, updateTable);

function updateTable() {
  tableRef.value.requestServerInteraction();
}

function onRequest(props: TableRequestProps) {
  const { page, rowsPerPage, sortBy, descending } = props.pagination;

  const skip = (page - 1) * rowsPerPage;
  const limit = rowsPerPage;
  loading.value = true;

  void catalogStore.loadSpaces(skip, limit).then((result: SpacesResult) => {
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
</script>
