<template>
  <div class="filter-section" style="--columns: 1">
    <div class="pollutants-section">
      <div class="filter-section__heading">
        {{ t('filter_dialog.parameters') }} · <span class="text-lowercase">{{ t('filter_dialog.pick_several') }}</span>
      </div>
      <FacetList
        v-model="draft.parameters"
        :options="parameterOptions"
        :limit="10"
        searchable
        search-keys
        sortable
        :search-placeholder="t('filter_dialog.search_parameters', { count: parameterOptions.length })"
      />
      <p class="filter-section__note">{{ t('filter_dialog.parameters_note') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
/** What is measured: the pollutants and other parameters. */
import FacetList from '@/components/filters/FacetList.vue';
import { toOptions } from '@/components/filters/facets';
import { FILTER_DRAFT } from '@/composables/useFilterDraft';
import { useFacetCounts } from '@/composables/useFacetCounts';

const { t } = useI18n();
const exploreStore = useExploreStore();
const draft = inject(FILTER_DRAFT)!;

const parameters = useFacetCounts(draft, { by: ['parameter'], own: ['parameters'] });

const parameterOptions = computed(() => toOptions(parameters.counts.value, exploreStore.parameterLabel));
</script>

<style scoped lang="scss">
.pollutants-section {
  max-width: 560px;
}
</style>
