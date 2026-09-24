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
      <span v-if="availableLabels">{{
        t('plots.available_parameters', { parameters: availableLabels })
      }}</span>
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
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components';
import { initOptions, updateOptions } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';
import { DEFAULT_MEASUREMENT_YEARS } from '@/stores/filters';
import type { ExploreParams } from '@/models';

use([SVGRenderer, BarChart, GridComponent, LegendComponent, TooltipComponent]);

interface Props {
  /** height of the plot area */
  height?: number;
}

withDefaults(defineProps<Props>(), { height: 400 });
const { t, locale } = useI18n();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

/** the biggest pollutants get a color each, the rest stack as "Other" */
const PALETTE = ['#4f8fcc', '#e8a33d', '#5aa469', '#c05b7b', '#8a6fc4'];
const OTHER_COLOR = '#bdbdbd';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';
const MONTHS = Array.from({ length: 12 }, (_, i) => String(i + 1));

function params(): ExploreParams | null {
  if (!exploreStore.dimension('month_of_year')) return null;
  const next: ExploreParams = {
    agg: 'count',
    by: ['month_of_year', 'parameter'],
    grain: 'day',
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

const monthNames = computed(() => {
  const format = new Intl.DateTimeFormat(locale.value, {
    month: 'short',
    timeZone: 'UTC',
  });
  return MONTHS.map((m) => format.format(new Date(Date.UTC(2000, +m - 1, 1))));
});

function formatCount(value: number): string {
  return value.toLocaleString(locale.value);
}

/** axis ticks: 2M rather than 2,000,000 */
function formatCompact(value: number): string {
  return new Intl.NumberFormat(locale.value, { notation: 'compact' }).format(
    value,
  );
}

/** records per month (index 0 = January), per pollutant slug */
const table = computed(() => {
  const rows = new Map<string, number[]>();
  for (const bucket of result.value?.buckets || []) {
    const [month, slug] = bucket.key;
    const index = month ? MONTHS.indexOf(month) : -1;
    if (index < 0 || !slug) continue;
    let row = rows.get(slug);
    if (!row) {
      row = new Array<number>(12).fill(0);
      rows.set(slug, row);
    }
    row[index] = (row[index] ?? 0) + (bucket.n_records ?? 0);
  }
  return rows;
});

const totals = computed(() => {
  const sums = new Array<number>(12).fill(0);
  for (const row of table.value.values())
    row.forEach((value, i) => (sums[i] = (sums[i] ?? 0) + value));
  return sums;
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

const availableLabels = computed(() =>
  (result.value?.meta.available_parameters || [])
    .map(exploreStore.parameterLabel)
    .join(', '),
);

/** total records, and the busiest month against the monthly average */
const summary = computed(() => {
  const sums = totals.value;
  const total = sums.reduce((a, b) => a + b, 0);
  if (!total) return '';
  const peak = sums.indexOf(Math.max(...sums));
  const lift = Math.round(((sums[peak] ?? 0) / (total / 12) - 1) * 100);
  return `${formatCompact(total)} ${t('plots.records').toLowerCase()} · ${t(
    'plots.peak_month',
    { month: monthNames.value[peak], lift: `+${lift}%` },
  )}`;
});

const option = computed<EChartsOption>(() => {
  const rows = table.value;
  const names = monthNames.value;
  if (!rows.size) {
    return {};
  }
  // biggest pollutant at the bottom of the stack
  const sorted = [...rows.keys()].sort(
    (a, b) =>
      (rows.get(b) ?? []).reduce((x, y) => x + y, 0) -
      (rows.get(a) ?? []).reduce((x, y) => x + y, 0),
  );
  // past the palette, the smaller pollutants fold into one "Other" band
  const folds = sorted.length > PALETTE.length;
  const kept = folds ? sorted.slice(0, PALETTE.length - 1) : sorted;
  const bands = kept.map((slug, i) => ({
    name: exploreStore.parameterLabel(slug),
    color: PALETTE[i] ?? OTHER_COLOR,
    data: rows.get(slug) ?? [],
  }));
  if (folds) {
    const other = new Array<number>(12).fill(0);
    for (const slug of sorted.slice(kept.length))
      (rows.get(slug) ?? []).forEach(
        (v, i) => (other[i] = (other[i] ?? 0) + v),
      );
    bands.push({
      name: t('plots.other_pollutants', sorted.length - kept.length),
      color: OTHER_COLOR,
      data: other,
    });
  }
  const stacked = bands.length > 1;
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const items = (Array.isArray(params) ? params : [params]).filter(
          (p) => Number(p.value) > 0,
        );
        const first = items[0];
        if (!first) return '';
        const lines = [`<b>${first.name}</b>`];
        for (const item of [...items].reverse())
          lines.push(
            `${item.marker as string}${item.seriesName}: <b>${formatCount(Number(item.value))}</b>`,
          );
        if (stacked)
          lines.push(
            `${t('plots.records')}: <b>${formatCount(totals.value[first.dataIndex] ?? 0)}</b>`,
          );
        return lines.join('<br/>');
      },
    },
    legend: {
      show: stacked,
      type: 'scroll',
      top: 0,
      left: 0,
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 16,
      textStyle: { color: TEXT },
      pageIconColor: MUTED,
      pageTextStyle: { color: MUTED },
      data: bands.map((band) => band.name),
    },
    grid: {
      left: 8,
      right: 8,
      // room for the legend row, then for the total labels
      top: stacked ? 56 : 24,
      bottom: 8,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: names,
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel: { color: TEXT },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED, formatter: (v: number) => formatCompact(v) },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: bands.map((band, i) => ({
      type: 'bar' as const,
      name: band.name,
      stack: 'records',
      data: band.data,
      barCategoryGap: '30%',
      cursor: 'default',
      // round the top of the stack only
      itemStyle: {
        color: band.color,
        borderRadius: i === bands.length - 1 ? [4, 4, 0, 0] : 0,
      },
      label: {
        show: i === bands.length - 1,
        position: 'top' as const,
        color: TEXT,
        formatter: (p: { dataIndex: number }) =>
          formatCompact(totals.value[p.dataIndex] ?? 0),
      },
    })),
  };
});
</script>
