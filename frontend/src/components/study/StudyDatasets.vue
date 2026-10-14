<template>
  <div>
    <q-table
      ref="tableRef"
      flat
      responsive
      :rows="rows"
      :columns="columms"
      v-model:pagination="pagination"
      :rows-per-page-options="[10, 25, 50, 100]"
      :loading="loading"
      row-key="id"
      @request="onRequest"
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

<script setup lang="ts">
import type { Dataset, Variable } from '@/models';
import { truncateString } from '@/utils/strings';
import { useStudyItemsTable } from '@/composables/useStudyItemsTable';

const { t } = useI18n();

const { tableRef, rows, loading, pagination, onRequest } = useStudyItemsTable<Dataset>('datasets', 'id');

const columms = computed(() => {
  return [
    {
      name: 'name',
      label: t('study.dataset.name'),
      align: 'left' as const,
      sortable: true,
      field: 'name',
    },
    {
      name: 'description',
      label: t('study.dataset.description'),
      align: 'left' as const,
      sortable: true,
      field: 'description',
      format: (v: string) => {
        return truncateString(v, 100);
      },
    },
    {
      name: 'variables',
      label: t('study.dataset.variables'),
      align: 'left' as const,
      field: 'variables',
      format: (v: Variable[]) => {
        return v?.length || 0;
      },
    },
  ];
});

</script>
