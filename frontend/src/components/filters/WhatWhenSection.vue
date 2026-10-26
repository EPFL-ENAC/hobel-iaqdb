<template>
  <div class="filter-section">
    <div>
      <div class="filter-section__heading">
        {{ t('filter_dialog.parameters') }} · <span class="text-lowercase">{{ t('filter_dialog.pick_several') }}</span>
      </div>
      <FacetList v-model="draft.parameters" :options="parameterOptions" :limit="10" />
    </div>
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.measurement_year') }}</div>
      <RangeHistogram
        v-model="draft.measurement_years"
        :min="DEFAULT_MEASUREMENT_YEARS.min"
        :max="DEFAULT_MEASUREMENT_YEARS.max"
        :bins="yearBins"
        :width="1"
        :caption="isAllYears ? t('filter_dialog.all_years') : ''"
      />
      <p class="filter-section__note">{{ t('filter_dialog.year_note') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
/** What is measured (the pollutants) and when (the measurement years). */
import FacetList from '@/components/filters/FacetList.vue';
import RangeHistogram from '@/components/filters/RangeHistogram.vue';
import { toOptions } from '@/components/filters/facets';
import { FILTER_DRAFT } from '@/composables/useFilterDraft';
import { useFacetCounts } from '@/composables/useFacetCounts';
import { DEFAULT_MEASUREMENT_YEARS } from '@/stores/filters';

const { t } = useI18n();
const exploreStore = useExploreStore();
const draft = inject(FILTER_DRAFT)!;

const parameters = useFacetCounts(draft, { by: ['parameter'], own: ['parameters'] });
const years = useFacetCounts(draft, { by: ['year'], own: ['measurement_years'], count: 'records' });

const parameterOptions = computed(() => toOptions(parameters.counts.value, exploreStore.parameterLabel));

/** records per year, keyed by the year */
const yearBins = computed(
  () => new Map([...years.counts.value].flatMap(([key, n]) => (key ? [[Number(key.slice(0, 4)), n] as const] : []))),
);

const isAllYears = computed(
  () =>
    draft.measurement_years.min === DEFAULT_MEASUREMENT_YEARS.min &&
    draft.measurement_years.max === DEFAULT_MEASUREMENT_YEARS.max,
);
</script>
