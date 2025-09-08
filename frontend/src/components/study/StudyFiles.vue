<template>
  <div>
    <div class="row">
      <q-btn
        v-if="authStore.isAdmin"
        flat
        color="primary"
        icon="download"
        no-caps
        :label="t('download')"
        class=""
      />
      <q-space />
      <q-input
        ref="filterRef"
        v-model="filter"
        label="Filter"
        style="width: 200px"
        dense
      >
        <template v-slot:append>
          <q-icon
            v-if="filter !== ''"
            name="clear"
            class="cursor-pointer"
            @click="resetFilter"
          />
        </template>
      </q-input>
    </div>

    <q-card flat bordered class="q-mt-md bg-grey-2">
      <q-card-section>
        <q-tree
          :nodes="simple"
          node-key="label"
          :filter="filter"
          default-expand-all
        />
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import { getSizeLabel } from 'src/utils/numbers';

const { t } = useI18n();
const catalogStore = useCatalogStore();
const authStore = useAuthStore();

const filter = ref('');
const filterRef = ref(null);

const study = computed(() => catalogStore.study);
const datasets = computed(() => catalogStore.study?.datasets || [])

const simple = computed(() => [
  {
    label: study.value?.name || '',
    children: [
      { label: 'README.md' },
      { label: 'LICENSE.md' },
      { label: 'study.json' },
      {
        label: 'datasets',
        children: datasets.value.map((ds) => {
          return {
            label: ds.name || '',
            children: ds.folder?.children?.map((f) => {
              return { label: `${f.name} (${getSizeLabel(f.size)})` }
            }) || [],
          }
        }),
      },
    ],
  },
]);

function resetFilter() {
  filter.value = '';
}
</script>
