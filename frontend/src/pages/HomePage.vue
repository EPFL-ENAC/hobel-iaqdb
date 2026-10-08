<template>
  <q-page>
    <app-header url="interior-1.jpg" />
    <div class="row">
      <div class="col"></div>
      <div class="col-8">
        <q-card flat class="q-mt-lg">
          <q-card-section>
            <q-markdown no-heading-anchor-links :src="IntroductionMd" />
          </q-card-section>
          <q-card-section>
            <div class="text-bold q-mb-md">{{ t('contact_information') }}</div>
            <div class="row q-gutter-lg">
              <div
                v-for="contact in contacts"
                :key="contact.url"
                class="contact text-center"
              >
                <q-img
                  :src="contact.portrait"
                  :alt="contact.name"
                  :ratio="3 / 4"
                  class="rounded-borders"
                />
                <a
                  :href="contact.url"
                  target="_blank"
                  class="epfl q-mt-sm inline-block"
                  >{{ contact.name }}</a
                >
              </div>
            </div>
          </q-card-section>
        </q-card>
        <q-btn
          flat
          color="primary"
          :label="t('search_catalog')"
          to="/data-hub"
        />
      </div>
      <div class="col"></div>
    </div>
    <div class="q-pa-md"></div>
  </q-page>
</template>

<script setup lang="ts">
import IntroductionMd from '@/assets/introduction.md';
import AppHeader from '@/components/AppHeader.vue';

const { t } = useI18n();

const contacts = [
  {
    name: 'Dr. Chenxi Liao',
    url: 'https://people.epfl.ch/chenxi.liao',
    portrait: 'portrait_chenxi.jpg',
  },
  {
    name: 'Prof. Dusan Licina',
    url: 'https://people.epfl.ch/dusan.licina',
    portrait: 'portrait_dusan.jpg',
  },
];
</script>

<style scoped>
.contact {
  width: 180px;
}
</style>
