<template>
  <div class="filter-section" style="--columns: 3">
    <div v-for="group in groups" :key="group.field">
      <div class="filter-section__heading">
        {{ group.heading }}<template v-if="group.filled !== null"> · {{ t('filter_dialog.filled', { share: formatShare(group.filled) }) }}</template>
      </div>
      <FacetChips v-model="draft[group.field]" :options="group.options" />
    </div>
  </div>
</template>

<script setup lang="ts">
/** Who uses the buildings and what surrounds them, with how often it is reported. */
import FacetChips from '@/components/filters/FacetChips.vue';
import { notReported, toOptions } from '@/components/filters/facets';
import { keyLabel } from '@/components/plots/charts';
import { FILTER_DRAFT } from '@/composables/useFilterDraft';
import { useChartFormat } from '@/composables/useChartFormat';
import { useFacetCounts } from '@/composables/useFacetCounts';

const { t } = useI18n();
const { formatShare } = useChartFormat();
const draft = inject(FILTER_DRAFT)!;

const DESCRIPTORS = [
  { field: 'outdoor_envs', dimension: 'outdoor_env', heading: 'filter_dialog.outdoor_env' },
  { field: 'age_groups', dimension: 'age_group', heading: 'filter_dialog.age_group' },
  { field: 'socioeconomic_status', dimension: 'socioeconomic_status', heading: 'filter_dialog.socioeconomic_status' },
] as const;

const facets = DESCRIPTORS.map((d) => ({ ...d, counts: useFacetCounts(draft, { by: [d.dimension], own: [d.field] }) }));

const groups = computed(() =>
  facets.map((facet) => {
    const counts = facet.counts.counts.value;
    const options = toOptions(counts, (key) => keyLabel(facet.dimension, key));
    const unknown = notReported(counts, t('filter_dialog.not_reported'));
    return {
      field: facet.field,
      heading: t(facet.heading),
      filled: facet.counts.filled.value,
      options: unknown ? [...options, unknown] : options,
    };
  }),
);
</script>
