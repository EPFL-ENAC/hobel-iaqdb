<template>
  <q-layout view="hHh lpR fFf">
    <q-header bordered class="bg-white text-grey-10">
      <app-toolbar @toggle="toggleLeftDrawer" />
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      :mini="!leftDrawerOpen || miniState"
      show-if-above
      bordered
    >
      <div v-if="!miniState">
        <q-list>
          <q-item-label header class="text-h6 q-ml-md q-pl-xs">{{
            $t('filters')
          }}</q-item-label>
        </q-list>
        <experiment-filters></experiment-filters>
      </div>
      <div
        v-if="!$q.screen.lt.md"
        class="absolute"
        style="top: 10px; right: 10px"
      >
        <q-btn
          dense
          round
          unelevated
          :icon="miniState ? 'chevron_right' : 'chevron_left'"
          @click="miniState = !miniState"
        />
      </div>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import AppToolbar from 'src/components/AppToolbar.vue';

const leftDrawerOpen = ref(false)
const miniState = ref(false)

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value
}
</script>
