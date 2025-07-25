<template>
  <q-toolbar class="bg-warning">
    <div>
      <q-icon name="warning" class="on-left q-mb-xs" />Note: this is a
      preliminary version. A lot of functionalities are mocked, to
      experiment/propose what could be the final user interface. Make any
      suggestions at:
      <a
        href="https://github.com/EPFL-ENAC/hobel-iaqdb/issues"
        target="_blank"
        class="text-bold epfl"
        >HOBEL IAQDB project <q-icon name="arrow_outward" /></a
      >.
    </div>
  </q-toolbar>
  <q-toolbar>
    <q-btn
      v-if="$q.screen.lt.md && !noMenu"
      flat
      dense
      round
      icon="menu"
      class="on-left"
      @click="toggleLeftDrawer"
    />
    <a href="https://epfl.ch" target="_blank" class="q-mt-sm">
      <img src="/EPFL_logo.png" :style="`height: ${$q.screen.lt.md ? '15px' : '25px'}`" />
    </a>
    <span class="q-ml-md text-bold q-mt-xs" :style="`font-size: ${$q.screen.lt.md ? '1.3em' : '1.5em'}`">{{ t('app_title') }}</span>
    <q-tabs
      v-if="!$q.screen.lt.sm"
      shrink
      stretch
      active-color="primary"
      class="q-ml-md"
    >
      <q-route-tab :label="t('home')" :title="t('home_info')" to="/" exact />
      <q-route-tab :label="t('data_hub')" :title="t('data_hub_info')" to="/data-hub" exact />
      <q-route-tab :label="t('explore')" :title="t('explore_info')" to="/explore" exact />
      <q-route-tab :label="t('contribute')" :title="t('contribute_info')" to="/contribute" exact />
    </q-tabs>
    <q-space />
    <span v-if="!$q.screen.lt.md">
      <q-btn
        flat
        round
        icon="menu_book"
        :title="t('resources')"
        @click="showResources = true"
      ></q-btn>
      <q-btn
        flat
        round
        icon="info"
        :title="t('introduction')"
        @click="showIntro = true"
      ></q-btn>
      <q-btn
        flat
        round
        icon="settings"
        :to="'/admin'"
        class="on-left"
      ></q-btn>
    </span>
    <q-btn v-if="$q.screen.lt.md" flat round icon="more_vert">
      <q-popup-proxy>
        <q-list class="bg-white">
          <q-item v-if="$q.screen.lt.sm" clickable v-close-popup to="/">
            <q-item-section>
              <q-item-label>{{ t('home') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item v-if="$q.screen.lt.sm" clickable v-close-popup to="/data-hub">
            <q-item-section>
              <q-item-label>{{ t('data_hub') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item v-if="$q.screen.lt.sm" clickable v-close-popup to="/explore">
            <q-item-section>
              <q-item-label>{{ t('explore') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item
            v-if="$q.screen.lt.sm"
            clickable
            v-close-popup
            to="/contribute"
          >
            <q-item-section>
              <q-item-label>{{ t('contribute') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-separator v-if="$q.screen.lt.sm" />
          <q-item clickable v-close-popup @click="showResources = true">
            <q-item-section>
              <q-item-label>{{ t('resources') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item clickable v-close-popup @click="showIntro = true">
            <q-item-section>
              <q-item-label>{{ t('introduction') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item clickable v-close-popup :to="'/admin'">
            <q-item-section>
              <q-item-label>{{ t('administration') }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-popup-proxy>
    </q-btn>
    <a href="https://www.epfl.ch/labs/hobel/" target="_blank" class="q-mt-xs">
      <span class="text-logo q-mb-xs" :style="`font-size: ${$q.screen.lt.md ? '1.3em' : '2.3em'}`">HOBEL</span>
    </a>
    <q-btn
      v-if="$q.screen.lt.md && !noMenu && route.path === '/data-hub'"
      flat
      dense
      round
      icon="menu"
      class="on-right"
      @click="toggleRightDrawer"
    />
  </q-toolbar>

  <simple-dialog
    v-model="showIntro"
    size="md"
    :content="IntroductionMd"
  />

  <simple-dialog v-model="showResources" :title="t('resources')">
    <q-list separator>
      <essential-link
        v-for="link in essentialLinks"
        :key="link.title"
        v-bind="link"
      />
    </q-list>
  </simple-dialog>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import IntroductionMd from 'src/assets/introduction.md';
import essentialLinks from 'src/assets/links.json';
import EssentialLink from 'src/components/EssentialLink.vue';
import SimpleDialog from 'src/components/SimpleDialog.vue';
import type { Settings } from 'src/stores/settings';

interface Props {
  noMenu?: boolean;
}

withDefaults(defineProps<Props>(), {
  noMenu: false,
});
const emit = defineEmits(['toggle-left', 'toggle-right']);

const $q = useQuasar();
const { t } = useI18n();
const settingsStore = useSettingsStore();
const route = useRoute();

const showIntro = ref(false);
const showResources = ref(false);

onMounted(() => {
  if (!settingsStore.settings?.intro_shown) {
    showIntro.value = true;
    settingsStore.saveSettings({ intro_shown: true } as Settings);
  }
});

function toggleLeftDrawer() {
  emit('toggle-left');
}

function toggleRightDrawer() {
  emit('toggle-right');
}
</script>
