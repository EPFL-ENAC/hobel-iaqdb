<template>
  <div>
    <div class="row items-center no-wrap q-mb-xs">
      <span class="text-caption text-grey-8">{{ rangeLabel }}</span>
      <q-space />
      <span v-if="summary" class="text-caption text-grey-7">{{ summary }}</span>
    </div>
    <div v-if="error" class="text-negative text-caption">
      {{ t('plots.error') }}: {{ error }}
    </div>
    <div v-else-if="empty" class="text-grey-7 text-caption">
      {{
        parameterLabels
          ? t('plots.no_data_for', { parameters: parameterLabels })
          : t('plots.no_data')
      }}
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
import { LineChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, TooltipComponent } from 'echarts/components';
import { initOptions, updateOptions } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';
import { DEFAULT_MEASUREMENT_YEARS } from '@/stores/filters';
import type { ExploreParams } from '@/models';

use([SVGRenderer, LineChart, GridComponent, TooltipComponent]);

interface Props {
  /** height of the plot area */
  height?: number;
}

withDefaults(defineProps<Props>(), { height: 400 });
const { t, locale } = useI18n();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const LINE_COLOR = '#2f5596';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';

function params(): ExploreParams | null {
  if (!exploreStore.dimension('dataset')) return null;
  const next: ExploreParams = {
    agg: 'coverage',
    by: ['dataset'],
    filter: exploreFilter(),
    ...exploreRange(),
  };
  // none selected: every pollutant
  if (exploreStore.parameters.length)
    next.parameters = [...exploreStore.parameters];
  return next;
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

function formatCount(value: number): string {
  return value.toLocaleString(locale.value);
}

/** datasets added per year, by the year of their first measurement */
const added = computed(() => {
  const counts = new Map<number, number>();
  for (const bucket of result.value?.buckets || []) {
    const first = bucket.coverage?.first_at;
    if (!first) continue;
    const year = new Date(first).getUTCFullYear();
    counts.set(year, (counts.get(year) ?? 0) + 1);
  }
  return counts;
});

/** every year from the first to the last, gaps included */
const years = computed(() => {
  const keys = [...added.value.keys()];
  if (!keys.length) return [];
  const first = Math.min(...keys);
  const last = Math.max(...keys);
  return Array.from({ length: last - first + 1 }, (_, i) => first + i);
});

/** running total of datasets per year */
const cumulative = computed(() => {
  let total = 0;
  return years.value.map((year) => (total += added.value.get(year) ?? 0));
});

const rangeLabel = computed(() => {
  void filtersStore.updates;
  const { min, max } = filtersStore.measurement_years;
  const from = min > DEFAULT_MEASUREMENT_YEARS.min ? `${min}` : '';
  const to = max < DEFAULT_MEASUREMENT_YEARS.max ? `${max}` : '';
  if (!from && !to) return t('plots.all_years');
  if (from === to) return from;
  return from && to
    ? `${from} – ${to}`
    : from
      ? t('plots.since_year', { year: from })
      : t('plots.until_year', { year: to });
});

const parameterLabels = computed(() =>
  exploreStore.parameters.map(exploreStore.parameterLabel).join(', '),
);

/** total datasets and the span of years they cover */
const summary = computed(() => {
  const total = cumulative.value[cumulative.value.length - 1] ?? 0;
  if (!total) return '';
  return `${t('datasets_with_count', total)} · ${t('plots.year_span', {
    count: years.value.length,
  })}`;
});

const option = computed<EChartsOption>(() => {
  const labels = years.value;
  const totals = cumulative.value;
  if (!labels.length) {
    return {};
  }
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
          t('plots.added_in_year', {
            count: formatCount(added.value.get(year) ?? 0),
          }),
        ].join('<br/>');
      },
    },
    grid: { left: 8, right: 24, top: 24, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels.map(String),
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel: { color: TEXT },
    },
    yAxis: {
      type: 'value',
      name: t('plots.datasets').toLowerCase(),
      nameLocation: 'middle',
      nameGap: 40,
      nameTextStyle: { color: MUTED },
      minInterval: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: [
      {
        type: 'line',
        data: totals,
        symbol: 'circle',
        symbolSize: 7,
        cursor: 'default',
        lineStyle: { color: LINE_COLOR, width: 2.5 },
        itemStyle: { color: LINE_COLOR },
      },
    ],
  };
});
</script>
