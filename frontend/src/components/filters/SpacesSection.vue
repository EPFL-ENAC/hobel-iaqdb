<template>
  <div class="filter-section">
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.space_type') }}</div>
      <FacetList
        v-model="draft.space_types"
        :options="spaceTypeOptions"
        searchable
        :search-placeholder="t('filter_dialog.search_space_types', { count: spaceTypeOptions.length })"
      />
      <p class="filter-section__note">{{ t('filter_dialog.space_type_note') }}</p>
    </div>
    <div>
      <div class="filter-section__group">
        <div class="filter-section__heading">{{ heading('filter_dialog.occupancy', occupancy.filled.value) }}</div>
        <FacetChips v-model="draft.occupancies" :options="occupancyOptions" />
      </div>
      <div class="filter-section__group">
        <div class="filter-section__heading">{{ t('filter_dialog.ventilation_type') }}</div>
        <FacetList v-model="draft.mechanical_ventilation_types" :options="ventilationOptions" />
      </div>
      <div class="filter-section__group">
        <div class="filter-section__heading">
          {{ heading('filter_dialog.air_filtration', filtration.filled.value) }}
        </div>
        <FacetChips v-model="draft.air_filtrations" :options="filtrationOptions" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/** The measured spaces: what they are, how they are used, ventilated and filtered. */
import FacetChips from '@/components/filters/FacetChips.vue';
import FacetList from '@/components/filters/FacetList.vue';
import { sentence, withNotReported } from '@/components/filters/facets';
import { keyLabel } from '@/components/plots/charts';
import { FILTER_DRAFT } from '@/composables/useFilterDraft';
import { useChartFormat } from '@/composables/useChartFormat';
import { useFacetCounts } from '@/composables/useFacetCounts';

const { t } = useI18n();
const { formatShare } = useChartFormat();
const draft = inject(FILTER_DRAFT)!;

const spaceTypes = useFacetCounts(draft, { by: ['space_type'], own: ['space_types'] });
const occupancy = useFacetCounts(draft, { by: ['occupancy'], own: ['occupancies'] });
const ventilation = useFacetCounts(draft, { by: ['ventilation_type'], own: ['mechanical_ventilation_types'] });
const filtration = useFacetCounts(draft, { by: ['air_filtration'], own: ['air_filtrations'] });

/** "Space use · 79 % filled" */
function heading(key: string, filled: number | null): string {
  return filled === null ? t(key) : `${t(key)} · ${t('filter_dialog.filled', { share: formatShare(filled) })}`;
}

const notReportedLabel = computed(() => t('filter_dialog.not_reported'));

const spaceTypeOptions = computed(() =>
  withNotReported(spaceTypes.counts.value, (key) => sentence(keyLabel('space_type', key)), notReportedLabel.value),
);
const occupancyOptions = computed(() =>
  withNotReported(occupancy.counts.value, (key) => sentence(keyLabel('occupancy', key)), notReportedLabel.value),
);
const ventilationOptions = computed(() =>
  withNotReported(ventilation.counts.value, (key) => keyLabel('ventilation_type', key), notReportedLabel.value),
);
const filtrationOptions = computed(() =>
  withNotReported(filtration.counts.value, (key) => keyLabel('air_filtration', key), notReportedLabel.value),
);
</script>
