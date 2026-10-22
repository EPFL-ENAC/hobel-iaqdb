<template>
  <ChartCard :eyebrow="eyebrow" :title="title">
    <FigureFrame :height="height" :loading="loading" :error="error" :empty="empty ? t('plots.no_data') : ''">
      <e-charts autoresize :init-options="initOptions" :option="option" :update-options="updateOptions" />
    </FigureFrame>
    <template #footer>
      <ul class="monthly-figure__legend">
        <li v-for="band in bands" :key="band.key">
          <span class="monthly-figure__swatch" :style="`background: ${band.color};`" />{{ band.name }}
        </li>
      </ul>
    </template>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * Records per calendar month: the selected pollutants in the accent at the
 * bottom of each bar, every other parameter stacked above in grey.
 */
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, TooltipComponent } from 'echarts/components';
import ChartCard from '@/components/explore/ChartCard.vue';
import FigureFrame from '@/components/explore/FigureFrame.vue';
import { FIGURE_ACCENT, FIGURE_REST, GRID, MUTED, initOptions, updateOptions } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useExploreRequest } from '@/composables/useExploreQuery';

use([SVGRenderer, BarChart, GridComponent, TooltipComponent]);

interface Props {
  eyebrow: string;
  title: string;
  /** height of the plot area */
  height?: number;
}

withDefaults(defineProps<Props>(), { height: 260 });
const { t, locale } = useI18n();
const { formatCount, formatCompact } = useChartFormat();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const MONTHS = Array.from({ length: 12 }, (_, i) => String(i + 1));

const { result, loading, error, empty, load } = useExploreRequest('measurements');

/** Load the chart: on mount and when the filters are applied; every parameter, split once loaded. */
function reload(): void {
  if (!exploreStore.dimension('month_of_year')) return void load(null);
  void load({
    agg: 'count',
    by: ['month_of_year', 'parameter'],
    grain: 'day',
    filter: exploreFilter(),
    ...exploreRange(),
  });
}

onMounted(reload);
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(reload);
});

const monthNames = computed(() => {
  const format = new Intl.DateTimeFormat(locale.value, { month: 'short', timeZone: 'UTC' });
  return MONTHS.map((m) => format.format(new Date(Date.UTC(2000, +m - 1, 1))));
});

interface Band {
  key: string;
  name: string;
  color: string;
  /** records per month, January first */
  data: number[];
}

/** the selected pollutants, then the rest; with none selected, every parameter as one band */
const bands = computed<Band[]>(() => {
  const selected = new Set(exploreStore.parameters);
  const picked = new Array<number>(12).fill(0);
  const rest = new Array<number>(12).fill(0);
  for (const bucket of result.value?.buckets || []) {
    const [month, slug] = bucket.key;
    const index = month ? MONTHS.indexOf(month) : -1;
    if (index < 0 || !slug) continue;
    const row = !selected.size || selected.has(slug) ? picked : rest;
    row[index] = (row[index] ?? 0) + (bucket.n_records ?? 0);
  }
  if (!selected.size)
    return [{ key: 'all', name: t('explore_figures.all_parameters'), color: FIGURE_ACCENT, data: picked }];
  return [
    {
      key: 'selected',
      name: exploreStore.parameters.map(exploreStore.parameterLabel).join(', '),
      color: FIGURE_ACCENT,
      data: picked,
    },
    { key: 'rest', name: t('explore_figures.other_parameters'), color: FIGURE_REST, data: rest },
  ];
});

const option = computed<EChartsOption>(() => {
  if (!result.value?.buckets.length) return {};
  const names = monthNames.value;
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(0, 0, 0, 0.04)' } },
      formatter: (params) => {
        const items = Array.isArray(params) ? params : [params];
        const first = items[0];
        if (!first) return '';
        const lines = [`<b>${first.name}</b>`];
        let total = 0;
        for (const item of [...items].reverse()) {
          total += Number(item.value);
          lines.push(`${item.marker as string}${item.seriesName}: <b>${formatCount(Number(item.value))}</b>`);
        }
        if (items.length > 1) lines.push(`${t('plots.records')}: <b>${formatCount(total)}</b>`);
        return lines.join('<br/>');
      },
    },
    grid: { left: 0, right: 0, top: 12, bottom: 0, containLabel: true },
    xAxis: {
      type: 'category',
      data: names,
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel: { color: MUTED, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      splitNumber: 3,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED, fontSize: 11, formatter: (v: number) => formatCompact(v) },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: bands.value.map((band) => ({
      type: 'bar' as const,
      name: band.name,
      stack: 'records',
      data: band.data,
      barCategoryGap: '20%',
      cursor: 'default',
      itemStyle: { color: band.color },
      emphasis: { disabled: true },
    })),
  };
});
</script>

<style scoped lang="scss">
.monthly-figure__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 24px;
  margin: 0;
  padding: 0;
  list-style: none;
  color: $grey-10;

  li {
    display: inline-flex;
    align-items: center;
    // the global `li + li` margin is for prose lists
    margin: 0;
  }
}

.monthly-figure__swatch {
  width: 12px;
  height: 12px;
  margin-right: 8px;
}
</style>
