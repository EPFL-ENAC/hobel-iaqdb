<template>
  <div>
    <q-table
      flat
      responsive
      :rows="datasets"
      :columns="columms"
      v-model:pagination="pagination"
      row-key="id"
    >
      <template v-slot:header="props">
        <q-tr :props="props">
          <q-th auto-width />
          <q-th
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
          >
            {{ col.label }}
          </q-th>
        </q-tr>
      </template>

      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td auto-width>
            <q-btn flat size="sm" color="accent" round dense @click="props.expand = !props.expand" :icon="props.expand ? 'remove' : 'add'" />
          </q-td>
          <q-td
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
          >
            {{ col.value }}
          </q-td>
        </q-tr>
        <q-tr v-show="props.expand" :props="props">
          <q-td colspan="100%">
            <pre class="text-left">{{ props.row.variables }}</pre>
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyDatasets',
});
</script>
<script setup lang="ts">
import type { Variable } from 'src/models';
import { truncateString } from 'src/utils/strings';

const catalogStore = useCatalogStore();
const { t } = useI18n();

const pagination = ref({
  sortBy: 'id',
  descending: false,
  page: 1,
  rowsPerPage: 25,
});

const datasets = computed(() => catalogStore.datasets || []);

const columms = computed(() => {
  return [
    {
      name: 'name',
      label: t('study.dataset.name'),
      align: 'left',
      sortable: true,
      field: 'name',
    },
    {
      name: 'description',
      label: t('study.dataset.description'),
      align: 'left',
      sortable: true,
      field: 'description',
      format: (v: string) => {
        return truncateString(v, 100);
      },
    },
    {
      name: 'variables',
      label: t('study.dataset.variables'),
      align: 'left',
      sortable: true,
      field: 'variables',
      format: (v: Variable[]) => {
        return v?.length || 0;
      },
    },
  ];
});

</script>
