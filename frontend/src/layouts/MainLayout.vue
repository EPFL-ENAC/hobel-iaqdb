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
        <layers-drawer />
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

    <q-drawer
      v-model="helpStore.show"
      side="right"
      :width="$q.screen.lt.md ? 300 : 500"
      overlay
      elevated
    >
      <help-drawer />
      <div class="absolute" style="top: 10px; right: 10px">
        <q-btn dense round unelevated icon="close" @click="toggleRightDrawer" />
      </div>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import AppToolbar from 'src/components/AppToolbar.vue';
import LayersDrawer from 'src/components/LayersDrawer.vue';
import HelpDrawer from 'src/components/HelpDrawer.vue';

const helpStore = useHelpStore();

const leftDrawerOpen = ref(false);
const miniState = ref(false);

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

function toggleRightDrawer() {
  helpStore.show = !helpStore.show;
}
</script>
