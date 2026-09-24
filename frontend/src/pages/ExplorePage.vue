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
          <q-card flat bordered class="full-height">
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
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.records_by_pollutant') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.records_by_pollutant_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <CoverageBarChart v-if="exploreStore.schema" :height="600" />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.datasets_by_building_type') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.datasets_by_building_type_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <MetadataBarChart
                v-if="exploreStore.schema"
                entity="datasets"
                by="building_type"
                click="none"
                :height="600"
              />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.datasets_by_ventilation') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.datasets_by_ventilation_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <MetadataBarChart
                v-if="exploreStore.schema"
                entity="datasets"
                by="ventilation"
                orientation="vertical"
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
import CoverageBarChart from '@/components/plots/CoverageBarChart.vue';

const { t } = useI18n();
const exploreStore = useExploreStore();

onMounted(() => void exploreStore.loadSchema());
</script>
