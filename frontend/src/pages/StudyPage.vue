<template>
  <q-page>
    <div class="q-pt-md q-pb-md bg-accent text-white text-weight-light">
    <div class="row">
      <div class="col"></div>
      <div class="col-10">
        <span class="text-h4">{{ catalogStore.study?.name }}</span>
      </div>
      <div class="col"></div>
    </div>
    </div>
    <q-separator />
    <div class="row">
      <div class="col"></div>
      <div class="col-10">
        <study-view />
      </div>
      <div class="col"></div>
    </div>

  </q-page>
</template>

<script setup lang="ts">
import StudyView from 'src/components/study/StudyView.vue';

const catalogStore = useCatalogStore();
const route = useRoute();
watch(() => route.params.id, () => updateStudy);

onMounted(updateStudy)

function updateStudy() {
  catalogStore.loadStudy(route.params.id as string)
}

</script>