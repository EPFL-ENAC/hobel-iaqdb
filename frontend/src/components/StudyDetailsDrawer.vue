<template>
  <div class="q-pa-md">
    <div v-if="!catalogStore.study" class="q-gutter-md">
      <q-spinner-dots color="primary" size="30px" />
    </div>
    <div v-else>
      <q-toolbar class="q-pa-none">
        <q-toolbar-title>{{ catalogStore.study?.name }}</q-toolbar-title>
        <q-btn no-caps icon-right="open_in_new" color="primary" size="sm" :label="$t('more_details')" @click="onMoreDetails"/>
      </q-toolbar>
      <q-separator class="q-mb-md" />
      <study-details />
      <study-dialog v-model="showDialog" />
    </div>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyDetailsDrawer',
});
</script>
<script setup lang="ts">
import StudyDetails from 'src/components/study/StudyDetails.vue';
import StudyDialog from 'src/components/study/StudyDialog.vue';

const catalogStore = useCatalogStore();

const showDialog = ref(false);

function onMoreDetails() {
  if (!catalogStore.study) {
    return;
  }
  showDialog.value = true;
  //router.push('/study?id=' + catalogStore.study?.identifier);
}
</script>
