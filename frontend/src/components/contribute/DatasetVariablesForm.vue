<template>
  <div>
    <div v-if="warnings.length" class="q-mt-sm q-mb-sm">
      <q-card bordered class="bg-warning">
        <div>
          <div class="q-pl-md q-pr-md q-pt-md">
            <span class="text-bold on-left">Warnings</span>
            <span>Please fix the following issues as much as possible before proceeding.</span>
          </div>
          <ul>
            <li v-for="msg in warnings" :key="msg">{{ msg }}</li>
          </ul>
        </div>
      </q-card>
    </div>

    <q-table
      :rows="variables"
      :columns="columns"
      v-model:pagination="pagination"
      row-key="name"
      table-header-style="background-color: #f5f5f5"
      flat
      class="q-mt-sm"
    >
      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td key="name" :props="props">
            <span class="text-bold">{{ props.row.name }}</span>
          </q-td>
          <q-td key="unit" :props="props">
            {{ props.row.unit }}
            <q-popup-edit v-model="props.row.unit" buttons v-slot="scope">
              <q-input v-model="scope.value" dense autofocus />
            </q-popup-edit>
          </q-td>
          <q-td key="format" :props="props">
            {{ props.row.format }}
            <q-popup-edit v-model="props.row.format" buttons v-slot="scope">
              <q-input v-model="scope.value" dense autofocus />
            </q-popup-edit>
          </q-td>
          <q-td key="reference" :props="props">
            {{ getRefenceLabel(props.row.reference) }}
            <q-popup-edit v-model="props.row.reference" buttons v-slot="scope">
              <q-select
                v-model="scope.value"
                :options="referenceOptions"
                emit-value
                map-options
              />
            </q-popup-edit>
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { referenceOptions } from 'src/utils/options';
import type { Dataset, Variable } from 'src/models';

//const contrib = useContributeStore();

interface Props {
  modelValue: Dataset;
}
const props = defineProps<Props>();

const dataset = ref(props.modelValue);
const variables = ref<Variable[]>(props.modelValue.variables || []);
const pagination = ref({
  sortBy: 'id',
  descending: false,
  page: 1,
  rowsPerPage: 10,
});

const columns = computed(() => [
  { name: 'name', label: 'Name', field: 'name', align: 'left' as const, sortable: true },
  { name: 'unit', label: 'Unit', field: 'unit', align: 'left' as const, sortable: true },
  { name: 'format', label: 'Format', field: 'format', align: 'left' as const, sortable: true },
  { name: 'reference', label: 'Reference', field: 'reference', align: 'left' as const, sortable: true },
]);

const warnings = computed(() => {
  const rval = [];
  if (!variables.value.find((v) => v.reference === 'building')) {
    rval.push('Building ID is missing');
  }
  if (!variables.value.find((v) => v.reference === 'space')) {
    rval.push('Space ID is missing');
  }
  if (
    !variables.value.find((v) => v.reference === 'instrument')
  ) {
    rval.push('Instrument ID is missing');
  }
  if (!variables.value.find((v) => v.reference === 'timestamp')) {
    rval.push('Timestamp is missing');
  }
  return rval;
});

watch(
  () => props.modelValue,
  (value) => {
    dataset.value = value;
  },
);

watch(
  () => props.modelValue.variables,
  (value) => {
    variables.value = value || [];
  },
);

function getRefenceLabel(reference: string | undefined) {
  const opt = referenceOptions.find((opt) => opt.value === reference);
  return opt ? opt.label : '';
}

</script>