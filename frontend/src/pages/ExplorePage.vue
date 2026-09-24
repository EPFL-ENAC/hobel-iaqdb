<template>
  <q-page>
    <q-toolbar class="bg-accent text-white">
      <div>
        This section is under construction. For suggestions of useful plots and
        features, please file a
        <a
          href="https://github.com/EPFL-ENAC/hobel-iaqdb/issues"
          target="_blank"
          class="text-white text-bold epfl"
          >GitHub issue <q-icon name="arrow_outward" /></a
        >.
      </div>
    </q-toolbar>
    <div class="q-pa-md">
      <div class="row q-col-gutter-md">
        <div class="col-12 col-md-6">
          <q-card flat bordered>
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.datasets_by_country') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.datasets_by_country_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <MetadataBarChart
                v-if="exploreStore.schema"
                entity="datasets"
                by="country"
                :depth="1"
                :height="600"
              />
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import MetadataBarChart from '@/components/plots/MetadataBarChart.vue';

const { t } = useI18n();
const exploreStore = useExploreStore();

onMounted(() => void exploreStore.loadSchema());
</script>
