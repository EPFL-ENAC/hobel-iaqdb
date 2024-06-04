<template>
  <q-toolbar>
    <q-btn
      v-if="$q.screen.lt.md"
      flat
      dense
      round
      icon="menu"
      class="on-left"
      @click="toggleLeftDrawer"
    />
    <a href="https://epfl.ch" target="_blank" class="q-mt-sm">
      <img src="/EPFL_logo.png" style="height: 25px" />
    </a>
    <span class="q-ml-md text-h6">{{ $t('app_title') }}</span>
    <q-tabs v-if="!$q.screen.lt.sm" shrink stretch active-color="primary" class="q-ml-md">
      <q-route-tab
        to="/"
        :label="$t('home')"
        exact
      />
      <q-route-tab
        :label="$t('page1')"
        to="/page1"
        exact
      />
      <q-route-tab
        :label="$t('page2')"
        to="/page2"
        exact
      />
    </q-tabs>
    <q-space v-if="!$q.screen.lt.sm" />
    <span v-if="!$q.screen.lt.md">
      <q-btn
        flat
        round
        icon="account_circle"
        :title="$t('contact_us')"
        @click="showContact = true"
      />
      <q-btn
        flat
        round
        icon="menu_book"
        :title="$t('resources')"
        @click="showResources = true"
      ></q-btn>
      <q-btn
        flat
        round
        icon="info"
        :title="$t('introduction')"
        @click="showIntro = true"
      ></q-btn>
      <q-btn
        flat
        round
        icon="handshake"
        :title="$t('acknowledgements')"
        @click="showAcknowledgements = true"
        class="on-left"
      ></q-btn>
    </span>
    <q-btn 
      v-if="$q.screen.lt.md"
      flat
      round
      icon="more_vert">
      <q-popup-proxy>
        <q-list class="bg-white">
          <q-item v-if="$q.screen.lt.sm" clickable v-close-popup to="/">
            <q-item-section>
              <q-item-label>{{ $t('home') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item v-if="$q.screen.lt.sm" clickable v-close-popup to="/page1">
            <q-item-section>
              <q-item-label>{{ $t('page1') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item v-if="$q.screen.lt.sm" clickable v-close-popup to="/page2">
            <q-item-section>
              <q-item-label>{{ $t('page2') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-separator v-if="$q.screen.lt.sm" />
          <q-item clickable v-close-popup @click="showContact = true">
            <q-item-section>
              <q-item-label>{{ $t('contact_us') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item clickable v-close-popup @click="showResources = true">
            <q-item-section>
              <q-item-label>{{ $t('resources') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item clickable v-close-popup @click="showIntro = true">
            <q-item-section>
              <q-item-label>{{ $t('introduction') }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item clickable v-close-popup @click="showAcknowledgements = true">
            <q-item-section>
              <q-item-label>{{ $t('acknowledgements') }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-popup-proxy>
    </q-btn>
    <a href="https://epfl.ch/" target="_blank" class="q-mt-sm">
      <q-skeleton
        style="height: 30px; width: 100px"
        class="float-right q-mb-sm"/>
    </a>
  </q-toolbar>

  <simple-dialog
    v-model="showIntro"
    :title="$t('app_title')"
    :content="IntroductionMd"/>

  <simple-dialog
    v-model="showAcknowledgements"
    :title="$t('acknowledgements')"
    :content="AcknowledgementsMd"/>

  <simple-dialog
    v-model="showResources"
    :title="$t('resources')">
    <q-list separator>
      <essential-link
        v-for="link in essentialLinks"
        :key="link.title"
        v-bind="link"
      />
    </q-list>
  </simple-dialog>

  <simple-dialog
    v-model="showContact"
    :title="$t('contact_us')"
    :content="ContactMd"/>

</template>

<script lang="ts">
import { defineComponent } from 'vue';
export default defineComponent({
  components: { SimpleDialog },
  name: 'AppToolbar',
});
</script>
<script setup lang="ts">
import { getSettings, saveSettings } from 'src/utils/settings';
import ContactMd from 'src/assets/contact.md';
import IntroductionMd from 'src/assets/introduction.md';
import AcknowledgementsMd from 'src/assets/acknowledgements.md';
import essentialLinks from 'src/assets/links.json';
import EssentialLink from 'src/components/EssentialLink.vue';
import SimpleDialog from 'src/components/SimpleDialog.vue';

const emit = defineEmits(['toggle']);

const showIntro = ref(false);
const showResources = ref(false);
const showContact = ref(false);
const showAcknowledgements = ref(false);

onMounted(() => {
  const settings = getSettings();
  if (!settings.intro_shown) {
    showIntro.value = true;
    settings.intro_shown = true;
    saveSettings(settings);
  }
});

function toggleLeftDrawer() {
  emit('toggle');
}
</script>
