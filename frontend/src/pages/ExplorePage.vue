<template>
  <q-page>
    <ExploreHero>
      <template #actions>
        <q-btn
          outline
          no-caps
          icon="download"
          color="grey-10"
          :label="t('explore_download.button')"
          @click="showDownload = true"
        />
      </template>
    </ExploreHero>
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
    <ExploreChapter
      :title="t('explore_chapters.reference.title')"
      :lead="t('explore_chapters.reference.lead')"
    >
      <DistributionFigure
        v-if="exploreStore.schema"
        :eyebrow="t('explore_figures.distribution.eyebrow')"
        :title="t('explore_figures.distribution.title')"
      />
      <PatternFigure
        v-if="exploreStore.schema"
        :eyebrow="t('explore_figures.pattern.eyebrow')"
        :title="t('explore_figures.pattern.title')"
      />
    </ExploreChapter>
    <ExploreChapter
      :title="t('explore_chapters.relationships.title')"
      :lead="t('explore_chapters.relationships.lead')"
    >
      <FigureGrid :columns="3">
        <GroupFigure
          v-if="exploreStore.schema"
          :aspect="t('explore_figures.groups.ventilation.aspect')"
          :title="t('explore_figures.groups.ventilation.title')"
          by="ventilation_type"
        />
        <GroupFigure
          v-if="exploreStore.schema"
          :aspect="t('explore_figures.groups.climate.aspect')"
          :title="t('explore_figures.groups.climate.title')"
          by="climate_zone"
        />
        <GroupFigure
          v-if="exploreStore.schema"
          :aspect="t('explore_figures.groups.building.aspect')"
          :title="t('explore_figures.groups.building.title')"
          by="building_type"
        />
      </FigureGrid>
      <FigureGrid>
        <RelationshipFigure v-if="exploreStore.schema" :title="t('explore_figures.relationship.title')" />
        <CorrelationFigure
          v-if="exploreStore.schema"
          :eyebrow="t('explore_figures.correlation.eyebrow')"
          :title="t('explore_figures.correlation.title')"
        />
      </FigureGrid>
      <PairFigure
        v-if="exploreStore.schema"
        :eyebrow="t('explore_figures.pair.eyebrow')"
        :title="t('explore_figures.pair.title')"
      />
    </ExploreChapter>
    <DownloadDialog v-model="showDownload" />
  </q-page>
</template>

<script setup lang="ts">
import DownloadDialog from '@/components/DownloadDialog.vue';
import ExploreHero from '@/components/explore/ExploreHero.vue';
import ExploreChapter from '@/components/explore/ExploreChapter.vue';
import FigureGrid from '@/components/explore/FigureGrid.vue';
import MetadataFigure from '@/components/explore/MetadataFigure.vue';
import CoverageFigure from '@/components/explore/CoverageFigure.vue';
import PeriodFigure from '@/components/explore/PeriodFigure.vue';
import MonthlyFigure from '@/components/explore/MonthlyFigure.vue';
import AvailabilityFigure from '@/components/explore/AvailabilityFigure.vue';
import DistributionFigure from '@/components/explore/DistributionFigure.vue';
import PatternFigure from '@/components/explore/PatternFigure.vue';
import GroupFigure from '@/components/explore/GroupFigure.vue';
import RelationshipFigure from '@/components/explore/RelationshipFigure.vue';
import CorrelationFigure from '@/components/explore/CorrelationFigure.vue';
import PairFigure from '@/components/explore/PairFigure.vue';

const { t } = useI18n();
const exploreStore = useExploreStore();
const showDownload = ref(false);

onMounted(() => {
  void exploreStore.loadSchema();
  // chart labels of studies drilled into
  void exploreStore.loadStudyNames();
});
</script>
