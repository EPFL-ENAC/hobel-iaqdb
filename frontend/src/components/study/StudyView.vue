<template>
  <div>
    <q-card flat bordered class="q-mt-md bg-light-blue-1">
      <q-card-section>
        <q-markdown :src="study?.description" />
      </q-card-section>
    </q-card>

    <div class="row q-col-gutter-md q-mt-md">
      <div class="col-8">
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
          <q-tab name="files" :label="$t('files')" />
        </q-tabs>

        <q-separator />

        <q-tab-panels v-model="tab">
          <q-tab-panel name="buildings" class="q-pl-none q-pr-none">
            <study-buildings />
          </q-tab-panel>
          <q-tab-panel name="files" class="q-pl-none q-pr-none">
            <study-files />
          </q-tab-panel>
        </q-tab-panels>
      </div>
      <div class="col-4">
        <study-details />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyView',
});
</script>
<script setup lang="ts">
import StudyDetails from 'src/components/study/StudyDetails.vue';
import StudyBuildings from 'src/components/study/StudyBuildings.vue';
import StudyFiles from 'src/components/study/StudyFiles.vue';

const catalogStore = useCatalogStore();

const tab = ref('buildings');

const study = computed(() => catalogStore.study);
</script>
