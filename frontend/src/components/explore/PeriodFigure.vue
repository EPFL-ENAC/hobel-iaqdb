<template>
  <ChartCard
    :eyebrow="eyebrowText"
    :title="title"
    :note="t('explore_figures.measurement_period.reading')"
    :image="image"
  >
    <FigureFrame :height="height" :loading="loading" :error="error" :empty="empty ? t('plots.no_data') : ''">
      <e-charts autoresize :init-options="initOptions" :option="option" :update-options="updateOptions" />
    </FigureFrame>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * Datasets so far, year by year: each dataset counts from the year of its
 * first measurement, within the selected years and of the selected pollutants.
 * A dataset begun before the years counts from the first of them.
 */
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, TooltipComponent } from 'echarts/components';
import ChartCard from '@/components/explore/ChartCard.vue';
import { drawECharts, type FigureImage } from '@/components/explore/figureImage';
import FigureFrame from '@/components/explore/FigureFrame.vue';
import { FIGURE_ACCENT, GRID, MUTED, axisTitle, initOptions, plotGrid, updateOptions } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useExploreRequest } from '@/composables/useExploreQuery';

use([SVGRenderer, LineChart, GridComponent, TooltipComponent]);

interface Props {
  eyebrow: string;
  title: string;
  /** height of the plot area */
  height?: number;
}

const props = withDefaults(defineProps<Props>(), { height: 260 });
const { t } = useI18n();
const { formatCount, withPollutants } = useChartFormat();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();
/** the selected pollutants, which the figure counts together */
const eyebrowText = computed(() => withPollutants(props.eyebrow, exploreStore.parameters));

const { result, loading, error, empty, load } = useExploreRequest('measurements');

/** Load the chart: on mount and when the filters are applied. */
function reload(): void {
  void load({
    agg: 'coverage',
    by: ['dataset'],
    filter: exploreFilter(),
    ...exploreRange(),
    ...(exploreStore.parameters.length ? { parameters: [...exploreStore.parameters] } : {}),
  });
}

onMounted(reload);
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(reload);
});

/** the selected years, read again when the filters are applied */
const range = computed(() => {
  void filtersStore.updates;
  return { ...filtersStore.measurement_years };
});

/** datasets added per year, by the year of their first measurement, kept within the selected years */
const added = computed(() => {
  const counts = new Map<number, number>();
  const { min, max } = range.value;
  for (const bucket of result.value?.buckets || []) {
    const first = bucket.coverage?.first_at;
    if (!first) continue;
    // a naive timestamp: new Date() would read it as local time
    const year = Math.max(Number(first.slice(0, 4)), min);
    if (year > max) continue;
    counts.set(year, (counts.get(year) ?? 0) + 1);
  }
  return counts;
});

/** every year from the first to the last selected one, gaps included */
const years = computed(() => {
  const keys = [...added.value.keys()];
  if (!keys.length) return [];
  const first = Math.min(...keys);
  const last = range.value.max;
  return Array.from({ length: last - first + 1 }, (_, i) => first + i);
});

/** running total of datasets per year */
const cumulative = computed(() => {
  let total = 0;
  return years.value.map((year) => (total += added.value.get(year) ?? 0));
});

const option = computed<EChartsOption>(() => {
  const labels = years.value;
  if (!labels.length) return {};
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const item = Array.isArray(params) ? params[0] : params;
        if (!item) return '';
        const year = labels[item.dataIndex] ?? 0;
        return [
          `<b>${year}</b>`,
          `${t('plots.datasets')}: <b>${formatCount(Number(item.value))}</b>`,
          t('plots.added_in_year', { count: formatCount(added.value.get(year) ?? 0) }),
        ].join('<br/>');
      },
    },
    grid: plotGrid({ left: 0, right: 8, top: 12, bottom: 0 }),
    xAxis: {
      ...axisTitle('x', t('explore_figures.measurement_period.axis_x')),
      type: 'category',
      boundaryGap: false,
      data: labels.map(String),
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel: { color: MUTED, fontSize: 11 },
    },
    yAxis: {
      ...axisTitle('y', t('explore_figures.measurement_period.axis_y')),
      type: 'value',
      minInterval: 1,
      splitNumber: 2,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED, fontSize: 11 },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: [
      {
        type: 'line',
        data: cumulative.value,
        smooth: 0.4,
        showSymbol: false,
        cursor: 'default',
        lineStyle: { color: FIGURE_ACCENT, width: 2 },
        itemStyle: { color: FIGURE_ACCENT },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(74, 163, 154, 0.95)' },
              { offset: 1, color: 'rgba(74, 163, 154, 0.25)' },
            ],
          },
        },
      },
    ],
  };
});

/** the image draws the chart again, at its width */
const image = computed<FigureImage>(() => ({ draw: (width) => drawECharts(option.value, width, props.height) }));
</script>
