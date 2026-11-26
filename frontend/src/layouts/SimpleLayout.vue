<template>
  <q-layout view="hHh lpR fFf">
    <q-header bordered class="bg-white text-grey-10">
      <app-toolbar no-menu />
    </q-header>

    <q-drawer
      v-model="helpStore.show"
      side="right"
      overlay
      bordered
      :width="$q.screen.lt.md ? 300 : 440"
    >
      <div class="q-mt-xl">
        <help-drawer />
        <div class="absolute" style="top: 10px; right: 20px">
          <q-btn dense round unelevated icon="close" @click="helpStore.show = false" />
        </div>
      </div>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import AppToolbar from '@/components/AppToolbar.vue';
import HelpDrawer from '@/components/HelpDrawer.vue';

const $q = useQuasar();
const helpStore = useHelpStore();
</script>