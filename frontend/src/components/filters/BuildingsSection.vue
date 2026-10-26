<template>
  <div class="filter-section" style="--columns: 3">
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.building_type') }}</div>
      <FacetList v-model="draft.building_types" :options="typeOptions" />
    </div>
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.study') }}</div>
      <q-input
        v-model="studySearch"
        dense
        outlined
        clearable
        :placeholder="t('filter_dialog.search_studies', { count: studyOptions.length })"
        class="q-mb-md"
      >
        <template #prepend><q-icon name="search" size="18px" /></template>
      </q-input>
      <FacetChips v-model="draft.study_ids" :options="matchingStudies" :limit="studySearch ? Infinity : 5" />
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
  </div>
</template>

<script setup lang="ts">
/** Which buildings: their type, their study, when they were built. */
import FacetChips from '@/components/filters/FacetChips.vue';
import FacetList from '@/components/filters/FacetList.vue';
import RangeHistogram from '@/components/filters/RangeHistogram.vue';
import { toOptions } from '@/components/filters/facets';
import { keyLabel } from '@/components/plots/charts';
import { FILTER_DRAFT } from '@/composables/useFilterDraft';
import { useChartFormat } from '@/composables/useChartFormat';
import { useFacetCounts } from '@/composables/useFacetCounts';
import { DEFAULT_CONSTRUCTION_YEARS } from '@/stores/filters';

const { t } = useI18n();
const { formatShare } = useChartFormat();
const draft = inject(FILTER_DRAFT)!;

const types = useFacetCounts(draft, { by: ['building_type'], own: ['building_types'] });
const studies = useFacetCounts(draft, { by: ['study'], own: ['study_ids'] });
const decades = useFacetCounts(draft, { by: ['construction_decade'], own: ['construction_years'] });

const studySearch = ref<string | null>('');

const typeOptions = computed(() => toOptions(types.counts.value, (key) => keyLabel('building_type', key)));
const studyOptions = computed(() => toOptions(studies.counts.value, (key) => keyLabel('study', key)));
const matchingStudies = computed(() => {
  const needle = (studySearch.value || '').trim().toLowerCase();
  return needle ? studyOptions.value.filter((o) => o.label.toLowerCase().includes(needle)) : studyOptions.value;
});

const decadeBins = computed(
  () => new Map([...decades.counts.value].flatMap(([key, n]) => (key === null ? [] : [[Number(key), n] as const]))),
);

/** "Any year · 16 % not reported" */
const constructionCaption = computed(() => {
  const any =
    draft.construction_years.min === DEFAULT_CONSTRUCTION_YEARS.min &&
    draft.construction_years.max === DEFAULT_CONSTRUCTION_YEARS.max;
  const filled = decades.filled.value;
  const missing = filled === null || filled === 1 ? '' : t('filter_dialog.not_reported_share', { share: formatShare(1 - filled) });
  return [any ? t('filter_dialog.any_year') : '', missing].filter(Boolean).join(' · ');
});
</script>
