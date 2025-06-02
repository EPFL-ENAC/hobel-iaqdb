<template>
  <div>
    <q-card flat bordered class="q-mt-md bg-light-blue-1 q-mb-md">
      <q-card-section>
        <q-markdown :src="study?.description" />
      </q-card-section>
    </q-card>

    <div class="grid">
      <div class="item item1">
        <study-tabs />
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
import StudyTabs from 'src/components/study/StudyTabs.vue';

const catalogStore = useCatalogStore();

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
@media (min-width: 1024px) {
  .grid {
    grid-template-columns: 2fr 1fr;
    grid-template-areas: "item1 item2";
  }
}

.item {
  min-width: 0;
}

.item1 {
  grid-area: item1;
}

.item2 {
  grid-area: item2;
}
</style>