<template>
  <div class="q-pa-md">
    <q-toolbar class="q-pa-none">
      <q-toolbar-title>{{ catalogStore.study?.name }}</q-toolbar-title>
      <q-btn no-caps icon-right="arrow_forward" color="primary" size="sm" :label="$t('more_details')" @click="onMoreDetails"/>
    </q-toolbar>
    <q-separator class="q-mb-md" />
    <study-details />
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyDetailsDrawer',
});
</script>
<script setup lang="ts">
import StudyDetails from 'src/components/study/StudyDetails.vue';

const catalogStore = useCatalogStore();
const router = useRouter();

function onMoreDetails() {
  router.push('/study?id=' + catalogStore.study?.id);
}
</script>
