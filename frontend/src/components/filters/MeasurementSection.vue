<template>
  <div class="filter-section" style="--columns: 3">
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
      <div class="filter-section__heading">{{ heading('filter_dialog.instrument_grade', grades.filled.value) }}</div>
      <FacetChips v-model="draft.instrument_grades" :options="gradeOptions" />
      <p class="filter-section__note">{{ t('filter_dialog.instrument_note') }}</p>
    </div>
    <div>
      <div class="filter-section__heading">{{ heading('filter_dialog.placement', placements.filled.value) }}</div>
      <FacetList
        v-model="draft.placements"
        :options="placementOptions"
        :limit="5"
        searchable
        :search-placeholder="t('filter_dialog.search_placements', { count: placementOptions.length })"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/** How it was measured: the study, the grade of the instruments and where they sampled. */
import FacetChips from '@/components/filters/FacetChips.vue';
import FacetList from '@/components/filters/FacetList.vue';
import { sentence, toOptions, withNotReported } from '@/components/filters/facets';
import { keyLabel } from '@/components/plots/charts';
import { FILTER_DRAFT } from '@/composables/useFilterDraft';
import { useChartFormat } from '@/composables/useChartFormat';
import { useFacetCounts } from '@/composables/useFacetCounts';

const { t } = useI18n();
const { formatShare } = useChartFormat();
const draft = inject(FILTER_DRAFT)!;

const studies = useFacetCounts(draft, { by: ['study'], own: ['study_ids'] });
const grades = useFacetCounts(draft, { by: ['instrument_grade'], own: ['instrument_grades'] });
const placements = useFacetCounts(draft, { by: ['placement'], own: ['placements'] });

const studySearch = ref<string | null>('');

/** "Instrument grade · 88 % filled" */
function heading(key: string, filled: number | null): string {
  return filled === null ? t(key) : `${t(key)} · ${t('filter_dialog.filled', { share: formatShare(filled) })}`;
}

const notReportedLabel = computed(() => t('filter_dialog.not_reported'));

const studyOptions = computed(() => toOptions(studies.counts.value, (key) => keyLabel('study', key)));
const matchingStudies = computed(() => {
  const needle = (studySearch.value || '').trim().toLowerCase();
  return needle ? studyOptions.value.filter((o) => o.label.toLowerCase().includes(needle)) : studyOptions.value;
});
const gradeOptions = computed(() =>
  withNotReported(grades.counts.value, (key) => sentence(keyLabel('instrument_grade', key)), notReportedLabel.value),
);
const placementOptions = computed(() =>
  withNotReported(placements.counts.value, (key) => sentence(key), notReportedLabel.value),
);
</script>
