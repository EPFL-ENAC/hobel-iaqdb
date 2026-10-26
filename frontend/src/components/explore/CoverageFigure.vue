<template>
  <ChartCard :eyebrow="eyebrow" :title="title">
    <RankedBars
      :rows="rows"
      :limit="limit"
      :label-header="t('explore_figures.parameters')"
      :bar-header="t('explore_figures.records')"
      :columns="columns"
      :layout="layout"
      :format-value="formatCompact"
      :dialog-eyebrow="eyebrow"
      :dialog-title="title"
      :loading="loading"
    >
      <template v-if="error" #message>
        <span class="text-negative text-caption">{{ t('plots.error') }}: {{ error }}</span>
      </template>
      <template v-else-if="empty" #message>
        <span class="text-grey-7 text-caption">{{ t('plots.no_data') }}</span>
      </template>
    </RankedBars>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * Records per pollutant, ranked, with the share of the expected records that
 * are present. Only the selected pollutants are shown, or every one when
 * none is selected.
 */
import ChartCard from '@/components/explore/ChartCard.vue';
import RankedBars from '@/components/explore/RankedBars.vue';
import type { RankedColumn, RankedRow } from '@/components/explore/ranked';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type { ExploreBucket } from '@/models';

interface Props {
  eyebrow: string;
  title: string;
  /** rows shown before the rest are summed into "Other" */
  limit?: number;
  /** how a row is laid out: `stacked` for narrow figures */
  layout?: 'inline' | 'stacked';
}

withDefaults(defineProps<Props>(), { limit: 10, layout: 'inline' });
const { t } = useI18n();
const { formatCompact, formatShare } = useChartFormat();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

// the same request as the explore hero: they share the cache
const { result, loading, error, empty, load } = useExploreRequest('measurements');

/** Load the chart: on mount and when the filters are applied. */
function reload(): void {
  void load({
    agg: 'coverage',
    by: ['parameter'],
    filter: exploreFilter(),
    ...exploreRange(),
  });
}

onMounted(reload);
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(reload);
});

const rows = computed<RankedRow<ExploreBucket>[]>(() => {
  const selected = new Set(exploreStore.parameters);
  return (result.value?.buckets || [])
    .flatMap((bucket) => {
      const slug = bucket.key[0];
      if (!slug || (selected.size && !selected.has(slug))) return [];
      return [
        {
          key: slug,
          label: exploreStore.parameterLabel(slug),
          value: bucket.n_records ?? 0,
          data: bucket,
        },
      ];
    })
    .sort((a, b) => b.value - a.value);
});

/** present records over expected ones, summed over the rows */
function completeness(rows: RankedRow<ExploreBucket>[]): string {
  let present = 0;
  let missing = 0;
  for (const row of rows) {
    present += row.data.n_records ?? 0;
    missing += row.data.coverage?.n_missing ?? 0;
  }
  return present + missing ? formatShare(present / (present + missing)) : '–';
}

const columns = computed<RankedColumn<ExploreBucket>[]>(() => [
  { key: 'complete', header: t('explore_figures.complete'), format: completeness },
]);
</script>
