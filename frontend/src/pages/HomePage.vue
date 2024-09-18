<template>
  <q-page>
    <app-header url="interior-1.jpg" />
    <div class="row">
      <div class="col"></div>
      <div class="col-8">
        <q-card flat class="q-mt-lg">
          <q-card-section>
            <q-markdown no-heading-anchor-links :src="content" />
          </q-card-section>
        </q-card>
        <q-btn flat color="primary" :label="$t('search')" to="/map" />
      </div>
      <div class="col"></div>
    </div>
    <div class="q-pa-md"></div>
  </q-page>
</template>

<script setup lang="ts">
import AppHeader from 'src/components/AppHeader.vue';

const ReadmeMd =
  'https://raw.githubusercontent.com/EPFL-ENAC/hobel-iaqdb/main/README.md';

const content = ref();

onMounted(async () => {
  const response = await fetch(ReadmeMd);
  content.value = await response.text();
});
</script>
