<template>
  <div class="filter-section" style="--columns: 1">
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
/** When it was measured: a range of measurement years. */
import RangeHistogram from '@/components/filters/RangeHistogram.vue';
import { FILTER_DRAFT } from '@/composables/useFilterDraft';
import { useFacetCounts } from '@/composables/useFacetCounts';
import { DEFAULT_MEASUREMENT_YEARS } from '@/stores/filters';

const { t } = useI18n();
const draft = inject(FILTER_DRAFT)!;

const years = useFacetCounts(draft, { by: ['year'], own: ['measurement_years'], count: 'records' });

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
