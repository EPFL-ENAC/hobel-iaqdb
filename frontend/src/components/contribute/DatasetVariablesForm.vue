<template>
  <div>
    <q-table
      :rows="variables"
      :columns="columns"
      row-key="name"
      hide-bottom
      flat
      no-data-label="No variables" />
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'DatasetVariablesForm',
});
</script>
<script setup lang="ts">
import { Dataset, Variable } from 'src/models';

//const contrib = useContributeStore();

interface Props {
  modelValue: Dataset;
}
const props = defineProps<Props>();

const dataset = ref(props.modelValue);
const variables = ref<Variable[]>(props.modelValue.variables || []);

const columns = computed(() => [
  { name: 'name', label: 'Name', field: 'name', align: 'left', sortable: true },
  { name: 'type', label: 'Data Type', field: 'type', align: 'left', sortable: true },
  { name: 'unit', label: 'Unit', field: 'unit', align: 'left', sortable: true },
  { name: 'format', label: 'Format', field: 'format', align: 'left', sortable: true },
  { name: 'reference', label: 'Reference', field: 'reference', align: 'left', sortable: true },
]);

watch(
  () => props.modelValue,
  (value) => {
    dataset.value = value;
    variables.value = value.variables || [];
  },
);

</script>