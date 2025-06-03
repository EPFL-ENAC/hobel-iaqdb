<template>
  <div>
    <q-table
      flat
      responsive
      :rows="instruments"
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
            <pre class="text-left">{{ props.row.parameters }}.</pre>
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyInstruments',
});
</script>
<script setup lang="ts">
import type { InstrumentParameter } from 'src/models';
import { equipmentGradeOptions, placementOptions } from 'src/utils/options';

const catalogStore = useCatalogStore();
const { t } = useI18n();

const pagination = ref({
  sortBy: 'identifier',
  descending: false,
  page: 1,
  rowsPerPage: 25,
});

const instruments = computed(() => catalogStore.instruments || []);

const columms = computed(() => {
  return [
    {
      name: 'identifier',
      label: 'ID',
      align: 'left',
      sortable: true,
      field: 'identifier',
    },
    {
      name: 'manufacturer',
      label: t('study.instrument.manufacturer'),
      align: 'left',
      sortable: true,
      field: 'manufacturer',
    },
    {
      name: 'model',
      label: t('study.instrument.model'),
      align: 'left',
      sortable: true,
      field: 'model',
    },
    {
      name: 'equipment_grade_rating',
      label: t('study.instrument.equipment_grade'),
      align: 'left',
      sortable: true,
      field: 'equipment_grade_rating',
      format: (val: string) => equipmentGradeOptions.find((opt) => opt.value === val)?.label || val,
    },
    {
      name: 'placement',
      label: t('study.instrument.placement'),
      align: 'left',
      sortable: true,
      field: 'placement',
      format: (val: string) => placementOptions.find((opt) => opt.value === val)?.label || val,
    },
    {
      name: 'parameters',
      label: t('study.instrument.parameters'),
      align: 'left',
      sortable: true,
      field: 'parameters',
      format: (v: InstrumentParameter[]) => {
        return v?.length || 0;
      },
    },
  ];
});

</script>
