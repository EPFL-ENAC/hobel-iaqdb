<template>
  <div>
    <q-card flat bordered class="q-mt-md bg-light-blue-1 q-mb-md">
      <q-card-section>
        <q-markdown :src="study?.description" />
      </q-card-section>
    </q-card>

    <div class="grid">
      <div class="item item1">
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
            <q-scroll-area style="height: 500px; max-width: 100%;">
              <pre>{{ catalogStore.instruments }}</pre>
            </q-scroll-area>
          </q-tab-panel>
          <q-tab-panel name="datasets" class="q-pl-none q-pr-none">
            <q-scroll-area style="height: 500px; max-width: 100%;">
              <pre>{{ catalogStore.datasets }}</pre>
            </q-scroll-area>
          </q-tab-panel>
          <q-tab-panel name="files" class="q-pl-none q-pr-none">
            <study-files />
          </q-tab-panel>
        </q-tab-panels>
      </div>
      <div class="item item2">
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

<style scoped>
.grid {
  display: grid;
  gap: 1rem;
  max-width: 100%;
}

/* Default: small screens — 2 rows */
.grid {
  grid-template-areas:
    "item2"
    "item1";
}

/* Medium and up: 2 columns */
@media (min-width: 800px) {
  .grid {
    grid-template-columns: 2fr 1fr;
    grid-template-areas: "item1 item2";
  }
}

.item1 {
  grid-area: item1;
}

.item2 {
  grid-area: item2;
}
</style>