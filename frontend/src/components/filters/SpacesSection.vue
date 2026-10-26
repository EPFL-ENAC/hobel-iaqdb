<template>
  <div class="filter-section">
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.mechanical_ventilation') }}</div>
      <FacetChips v-model="draft.mechanical_ventilation" :options="ventilationOptions" single />
      <p class="filter-section__note">{{ t('filter_dialog.ventilation_note') }}</p>
    </div>
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.ventilation_type') }}</div>
      <FacetList v-model="draft.mechanical_ventilation_types" :options="typeOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
/** How the measured spaces are ventilated. */
import FacetChips from '@/components/filters/FacetChips.vue';
import FacetList from '@/components/filters/FacetList.vue';
import { notReported, toOptions } from '@/components/filters/facets';
import { keyLabel } from '@/components/plots/charts';
import { FILTER_DRAFT } from '@/composables/useFilterDraft';
import { useFacetCounts } from '@/composables/useFacetCounts';

const { t } = useI18n();
const draft = inject(FILTER_DRAFT)!;

const ventilation = useFacetCounts(draft, { by: ['ventilation'], own: ['mechanical_ventilation'] });
const types = useFacetCounts(draft, { by: ['ventilation_type'], own: ['mechanical_ventilation_types'] });

function withUnknown(counts: Map<string | null, number>, label: (key: string) => string) {
  const unknown = notReported(counts, t('filter_dialog.not_reported'));
  const options = toOptions(counts, label);
  return unknown ? [...options, unknown] : options;
}

const ventilationOptions = computed(() => withUnknown(ventilation.counts.value, (key) => keyLabel('ventilation', key)));
const typeOptions = computed(() => withUnknown(types.counts.value, (key) => keyLabel('ventilation_type', key)));
</script>
