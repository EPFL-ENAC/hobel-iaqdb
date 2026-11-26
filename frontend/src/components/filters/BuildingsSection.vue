<template>
  <div class="filter-section" style="--columns: 3">
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.building_type') }}</div>
      <FacetList v-model="draft.building_types" :options="typeOptions" />
    </div>
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.construction_year') }}</div>
      <RangeHistogram
        v-model="draft.construction_years"
        :min="DEFAULT_CONSTRUCTION_YEARS.min"
        :max="DEFAULT_CONSTRUCTION_YEARS.max"
        :bins="decadeBins"
        :width="10"
        :caption="constructionCaption"
      />
    </div>
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.mechanical_ventilation') }}</div>
      <FacetChips v-model="draft.mechanical_ventilation" :options="ventilationOptions" single />
      <p class="filter-section__note">{{ t('filter_dialog.ventilation_note') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
/** Which buildings: their type, when they were built, whether they are mechanically ventilated. */
import FacetChips from '@/components/filters/FacetChips.vue';
import FacetList from '@/components/filters/FacetList.vue';
import RangeHistogram from '@/components/filters/RangeHistogram.vue';
import { toOptions, withNotReported } from '@/components/filters/facets';
import { keyLabel } from '@/components/plots/charts';
import { FILTER_DRAFT } from '@/composables/useFilterDraft';
import { useChartFormat } from '@/composables/useChartFormat';
import { useFacetCounts } from '@/composables/useFacetCounts';
import { DEFAULT_CONSTRUCTION_YEARS } from '@/stores/filters';

const { t } = useI18n();
const { formatShare } = useChartFormat();
const draft = inject(FILTER_DRAFT)!;

const types = useFacetCounts(draft, { by: ['building_type'], own: ['building_types'] });
const decades = useFacetCounts(draft, { by: ['construction_decade'], own: ['construction_years'] });
const ventilation = useFacetCounts(draft, { by: ['ventilation'], own: ['mechanical_ventilation'] });

const typeOptions = computed(() => toOptions(types.counts.value, (key) => keyLabel('building_type', key)));
const ventilationOptions = computed(() =>
  withNotReported(ventilation.counts.value, (key) => keyLabel('ventilation', key), t('filter_dialog.not_reported')),
);

const decadeBins = computed(
  () => new Map([...decades.counts.value].flatMap(([key, n]) => (key === null ? [] : [[Number(key), n] as const]))),
);

/** "Any year · 16 % not reported" */
const constructionCaption = computed(() => {
  const any =
    draft.construction_years.min === DEFAULT_CONSTRUCTION_YEARS.min &&
    draft.construction_years.max === DEFAULT_CONSTRUCTION_YEARS.max;
  const filled = decades.filled.value;
  const missing =
    filled === null || filled === 1 ? '' : t('filter_dialog.not_reported_share', { share: formatShare(1 - filled) });
  return [any ? t('filter_dialog.any_year') : '', missing].filter(Boolean).join(' · ');
});
</script>
