<template>
  <div>
    <q-table
      ref="tableRef"
      flat
      grid
      :rows="rows"
      row-key="_id"
      v-model:pagination="pagination"
      :loading="loading"
      @request="onRequest"
      >

      <template v-slot:item="props">
        <div class="col-12">
          <q-card flat @click="onRowClick(props.row)" class="cursor-pointer">
            <q-card-section>
              <div class="text-h6">{{ props.row.name }}</div>
              <div class="text-subtitle1 text-grey-8">{{ props.row.description }}</div>
              <div>
                <q-chip color="secondary" class="text-white" :label="`${props.row.building_count} buildings`" />
                <q-chip color="accent" class="on-right text-white" :label="`${props.row.room_count} rooms`" />
                <q-chip class="on-right" :label="$t('from_to', { from: props.row.start_year, to: props.row.end_year })" />
              </div>
            </q-card-section>
          </q-card>
          <q-separator />
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
  sortBy: '_id',
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

function onRequest (props) {
  const { page, rowsPerPage, sortBy, descending } = props.pagination

  const skip = (page - 1) * rowsPerPage;
  const limit = rowsPerPage;
  loading.value = true

  catalogStore.loadStudies(skip, limit)
    .then((result: StudiesResult) => {
      rows.value = result.data;
      pagination.value.rowsNumber = result.total;

      // don't forget to update local pagination object
      pagination.value.page = page
      pagination.value.rowsPerPage = rowsPerPage
      pagination.value.sortBy = sortBy
      pagination.value.descending = descending

      // ...and turn of loading indicator
      loading.value = false
    });
}

function onRowClick(val: Study) {
  router.push(`/study/${val._id}`);
}
</script>