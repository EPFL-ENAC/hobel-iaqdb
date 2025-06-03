<template>
  <div>
    <q-tabs
      v-model="tab"
      dense
      class="text-grey"
      active-color="secondary"
      indicator-color="secondary"
      align="justify"
      narrow-indicator
    >
    <q-tab name="buildings" :label="$t('buildings')" />
    <q-tab name="instruments" :label="$t('instruments')" />
    <q-tab name="datasets" :label="$t('datasets')" />
      <q-tab name="files" :label="$t('files')" />
    </q-tabs>

    <q-separator />

    <q-tab-panels v-model="tab">
      <q-tab-panel name="buildings" class="q-pl-none q-pr-none">
        <study-buildings />
      </q-tab-panel>
      <q-tab-panel name="instruments" class="q-pl-none q-pr-none">
        <study-instruments />
      </q-tab-panel>
      <q-tab-panel name="datasets" class="q-pl-none q-pr-none">
        <study-datasets />
      </q-tab-panel>
      <q-tab-panel name="files" class="q-pl-none q-pr-none">
        <study-files />
      </q-tab-panel>
    </q-tab-panels>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyTabs',
});
</script>
<script setup lang="ts">
import StudyBuildings from 'src/components/study/StudyBuildings.vue';
import StudyInstruments from 'src/components/study/StudyInstruments.vue';
import StudyDatasets from 'src/components/study/StudyDatasets.vue';
import StudyFiles from 'src/components/study/StudyFiles.vue';

const catalogStore = useCatalogStore();

const tab = ref('buildings');
</script>
