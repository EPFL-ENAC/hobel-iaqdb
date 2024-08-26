<template>
  <q-page>
    <q-tabs
      v-model="tab"
      dense
      class="text-grey"
      active-color="secondary"
      indicator-color="secondary"
      align="justify"
      narrow-indicator
    >
      <q-tab name="studies" :label="$t('studies')" />
      <q-tab name="buildings" :label="$t('buildings')" />
      <q-tab name="spaces" :label="$t('spaces')" />
    </q-tabs>

    <q-separator />

    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="studies">
        <study-list />
      </q-tab-panel>
      <q-tab-panel name="buildings">
        <building-list />
      </q-tab-panel>
      <q-tab-panel name="spaces">
        <space-list />
      </q-tab-panel>
    </q-tab-panels>
    
  </q-page>
</template>

<script setup lang="ts">
import StudyList from 'src/components/StudyList.vue';
import BuildingList from 'src/components/BuildingList.vue';
import SpaceList from 'src/components/SpaceList.vue';

const tab = ref('studies');

</script>
