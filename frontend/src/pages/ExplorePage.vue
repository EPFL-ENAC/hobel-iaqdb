<template>
  <q-page>
    <ExploreHero />
    <ExploreChapter
      :title="t('explore_chapters.collection.title')"
      :lead="t('explore_chapters.collection.lead')"
    >
      <FigureGrid>
        <MetadataFigure
          v-if="exploreStore.schema"
          :eyebrow="t('explore_figures.datasets_by_country.eyebrow')"
          :title="t('explore_figures.datasets_by_country.title')"
          entity="datasets"
          :path="['country', 'city', 'study']"
          :with-parameters="false"
        />
        <CoverageFigure
          v-if="exploreStore.schema"
          :eyebrow="t('explore_figures.records_by_pollutant.eyebrow')"
          :title="t('explore_figures.records_by_pollutant.title')"
        />
      </FigureGrid>
      <FigureGrid :columns="3">
        <MetadataFigure
          v-if="exploreStore.schema"
          :eyebrow="t('explore_figures.datasets_by_building_type.eyebrow')"
          :title="t('explore_figures.datasets_by_building_type.title')"
          entity="datasets"
          :path="['building_type', 'country', 'city', 'study']"
          layout="stacked"
          :limit="4"
          :with-parameters="false"
        />
        <MetadataFigure
          v-if="exploreStore.schema"
          :eyebrow="t('explore_figures.datasets_by_climate_zone.eyebrow')"
          :title="t('explore_figures.datasets_by_climate_zone.title')"
          entity="datasets"
          :path="['climate_zone', 'country', 'city', 'study']"
          layout="stacked"
          :limit="4"
          :with-parameters="false"
        />
        <MetadataFigure
          v-if="exploreStore.schema"
          :eyebrow="t('explore_figures.datasets_by_ventilation.eyebrow')"
          :title="t('explore_figures.datasets_by_ventilation.title')"
          entity="datasets"
          :path="['ventilation', 'ventilation_type', 'space_type', 'study']"
          layout="stacked"
          :limit="4"
          :with-parameters="false"
        />
      </FigureGrid>
      <FigureGrid>
        <PeriodFigure
          :eyebrow="t('explore_figures.measurement_period.eyebrow')"
          :title="t('explore_figures.measurement_period.title')"
        />
        <MonthlyFigure
          v-if="exploreStore.schema"
          :eyebrow="t('explore_figures.records_by_month.eyebrow')"
          :title="t('explore_figures.records_by_month.title')"
        />
      </FigureGrid>
    </ExploreChapter>
    <ExploreChapter
      :title="t('explore_chapters.completeness.title')"
      :lead="t('explore_chapters.completeness.lead')"
    >
      <AvailabilityFigure
        :eyebrow="t('explore_figures.metadata_availability.eyebrow')"
        :title="t('explore_figures.metadata_availability.title')"
      />
    </ExploreChapter>
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
      <q-space />
      <q-btn
        outline
        no-caps
        icon="download"
        :label="t('explore_download.button')"
        @click="showDownload = true"
      />
    </q-toolbar>
    <DownloadDialog v-model="showDownload" />
    <div class="q-pa-md">
      <div class="row q-col-gutter-md">
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.descriptive_stats') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.descriptive_stats_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <DescriptiveStatsChart v-if="exploreStore.schema" :height="600" />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.benchmark_comparison') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.benchmark_comparison_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <BenchmarkChart v-if="exploreStore.schema" :height="600" />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.trends') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.trends_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <TrendChart
                v-if="exploreStore.schema"
                :height="320"
                :table-height="280"
              />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.exceedance_over_time') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.exceedance_over_time_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <ExceedanceChart v-if="exploreStore.schema" :height="600" />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.relationship') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.relationship_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <RelationshipChart v-if="exploreStore.schema" :height="600" />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.relationship_ventilation') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.relationship_ventilation_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <GroupMedianChart v-if="exploreStore.schema" :height="600" />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.relationship_climate') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.relationship_climate_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <GroupMedianChart
                v-if="exploreStore.schema"
                by="climate_zone"
                :height="600"
              />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.relationship_building_type') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.relationship_building_type_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <GroupMedianChart
                v-if="exploreStore.schema"
                by="building_type"
                orientation="horizontal"
                :height="600"
              />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.correlation_matrix') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.correlation_matrix_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <CorrelationMatrixChart v-if="exploreStore.schema" :height="600" />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height">
            <q-card-section class="q-pb-none">
              <div class="text-subtitle1 text-bold">
                {{ t('plots.custom_relationship') }}
              </div>
              <div class="text-caption text-grey-7">
                {{ t('plots.custom_relationship_hint') }}
              </div>
            </q-card-section>
            <q-card-section>
              <CustomRelationshipChart v-if="exploreStore.schema" :height="600" />
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import DescriptiveStatsChart from '@/components/plots/DescriptiveStatsChart.vue';
import BenchmarkChart from '@/components/plots/BenchmarkChart.vue';
import TrendChart from '@/components/plots/TrendChart.vue';
import ExceedanceChart from '@/components/plots/ExceedanceChart.vue';
import RelationshipChart from '@/components/plots/RelationshipChart.vue';
import GroupMedianChart from '@/components/plots/GroupMedianChart.vue';
import CorrelationMatrixChart from '@/components/plots/CorrelationMatrixChart.vue';
import CustomRelationshipChart from '@/components/plots/CustomRelationshipChart.vue';
import DownloadDialog from '@/components/DownloadDialog.vue';
import ExploreHero from '@/components/explore/ExploreHero.vue';
import ExploreChapter from '@/components/explore/ExploreChapter.vue';
import FigureGrid from '@/components/explore/FigureGrid.vue';
import MetadataFigure from '@/components/explore/MetadataFigure.vue';
import CoverageFigure from '@/components/explore/CoverageFigure.vue';
import PeriodFigure from '@/components/explore/PeriodFigure.vue';
import MonthlyFigure from '@/components/explore/MonthlyFigure.vue';
import AvailabilityFigure from '@/components/explore/AvailabilityFigure.vue';

const { t } = useI18n();
const exploreStore = useExploreStore();
const showDownload = ref(false);

onMounted(() => {
  void exploreStore.loadSchema();
  // chart labels of studies drilled into
  void exploreStore.loadStudyNames();
});
</script>
