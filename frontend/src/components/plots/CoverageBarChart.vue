<template>
  <div>
    <div class="row items-center no-wrap q-mb-xs">
      <span class="text-caption text-grey-8">{{ dimensionLabel }}</span>
      <q-space />
      <span v-if="summary" class="text-caption text-grey-7">{{ summary }}</span>
    </div>
    <div v-if="error" class="text-negative text-caption">
      {{ t('plots.error') }}: {{ error }}
    </div>
    <div v-else-if="empty" class="text-grey-7 text-caption">
      {{ t('plots.no_data') }}
    </div>
    <div v-else :style="`height: ${height}px;`">
      <e-charts
        autoresize
        :init-options="initOptions"
        :option="option"
        :update-options="updateOptions"
        :loading="loading"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, TooltipComponent } from 'echarts/components';
import { initOptions, updateOptions } from '@/components/plots/charts';
import { exploreFilter } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type { ExploreBucket, ExploreParams } from '@/models';

use([SVGRenderer, BarChart, GridComponent, TooltipComponent]);

interface Props {
  /** height of the plot area; the bars share it */
  height?: number;
}

interface BarItem {
  name: string;
  value: number;
  slug: string;
  missing: number;
  /** share of expected records that are present, 0..1 */
  completeness: number;
  bucket: ExploreBucket;
  itemStyle: { color: string };
}

withDefaults(defineProps<Props>(), { height: 200 });
const { t, locale } = useI18n();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const BAR_COLOR = '#4f8fcc';
const SELECTED_COLOR = '#2f6fa8';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';

const dimension = computed(() => exploreStore.dimension('parameter'));
const dimensionLabel = computed(() => dimension.value?.label || '');

function params(): ExploreParams | null {
  if (!dimension.value) return null;
  return { agg: 'coverage', by: ['parameter'], filter: exploreFilter() };
}

const { result, loading, error, empty, load } =
  useExploreRequest('measurements');

/** Load the chart: on mount and when the filters are applied. */
function reload(): void {
  void load(params());
}

onMounted(reload);
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(reload);
});

function completenessOf(bucket: ExploreBucket): number {
  const records = bucket.n_records ?? 0;
  const total = records + (bucket.coverage?.n_missing ?? 0);
  return total ? records / total : 0;
}

function formatCount(value: number): string {
  return value.toLocaleString(locale.value);
}

/** axis ticks: 2M rather than 2,000,000 */
function formatCompact(value: number): string {
  return new Intl.NumberFormat(locale.value, { notation: 'compact' }).format(
    value,
  );
}

function formatShare(value: number): string {
  return `${Math.round(value * 100)}%`;
}

const summary = computed(() => {
  const value = result.value;
  if (!value || value.meta.n === 0) return '';
  const records = value.buckets.reduce((sum, b) => sum + (b.n_records ?? 0), 0);
  const missing = value.buckets.reduce(
    (sum, b) => sum + (b.coverage?.n_missing ?? 0),
    0,
  );
  const total = records + missing;
  const pollutants = t('plots.levels.parameter', value.buckets.length);
  return total
    ? `${pollutants} · ${t('plots.complete', { share: formatShare(records / total) })}`
    : pollutants;
});

const option = computed<EChartsOption>(() => {
  const value = result.value;
  if (!value) {
    return {};
  }
  const selected = new Set(exploreStore.parameters);
  const items: BarItem[] = value.buckets
    .flatMap((bucket) => {
      const slug = bucket.key[0];
      if (!slug) return [];
      return [
        {
          name: exploreStore.parameterLabel(slug),
          value: bucket.n_records ?? 0,
          slug,
          missing: bucket.coverage?.n_missing ?? 0,
          completeness: completenessOf(bucket),
          bucket,
          itemStyle: { color: selected.has(slug) ? SELECTED_COLOR : BAR_COLOR },
        },
      ];
    })
    .sort((a, b) => b.value - a.value);
  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const item = (Array.isArray(params) ? params[0] : params)?.data as
          BarItem | undefined;
        if (!item) return '';
        const lines = [
          `<b>${item.name}</b>`,
          `${t('plots.records')}: <b>${formatCount(item.value)}</b>`,
          `${t('plots.missing')}: ${formatCount(item.missing)}`,
          `${t('plots.completeness')}: ${formatShare(item.completeness)}`,
          t('datasets_with_count', item.bucket.coverage?.n_datasets ?? 0),
        ];
        return lines.join('<br/>');
      },
    },
    grid: { left: 8, right: 110, top: 8, bottom: 8, containLabel: true },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED, formatter: (v: number) => formatCompact(v) },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: items.map((item) => item.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: TEXT, width: 160, overflow: 'truncate' },
    },
    series: [
      {
        type: 'bar',
        data: items,
        barCategoryGap: '30%',
        cursor: 'default',
        itemStyle: { borderRadius: [0, 4, 4, 0] },
        label: {
          show: true,
          position: 'right',
          color: TEXT,
          formatter: (params) => {
            const item = params.data as BarItem;
            return `${formatCount(item.value)}  {muted|${formatShare(item.completeness)}}`;
          },
          rich: { muted: { color: MUTED } },
        },
      },
    ],
  };
});
</script>
