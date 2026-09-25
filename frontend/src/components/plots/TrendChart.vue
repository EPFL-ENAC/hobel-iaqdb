<template>
  <div>
    <div class="row items-center q-col-gutter-sm q-mb-sm">
      <div class="col-6 col-sm-3">
        <q-select
          :model-value="parameter"
          :options="parameterOptions"
          :label="t('plots.pollutant')"
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onParameter"
        />
      </div>
      <div class="col-6 col-sm-3">
        <q-select
          :model-value="year"
          :options="yearOptions"
          :label="t('plots.year')"
          :loading="yearsRequest.loading.value"
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onYear"
        />
      </div>
      <div class="col-6 col-sm-3">
        <q-select
          :model-value="context"
          :options="contextOptions"
          :label="t('plots.context')"
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onContext"
        />
      </div>
      <div class="col-6 col-sm-3">
        <q-select
          :model-value="contextValue"
          :options="valueOptions"
          :label="contextLabel"
          :disable="!context"
          :loading="valuesLoading"
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onValue"
        />
      </div>
    </div>
    <div class="row items-center no-wrap q-mb-xs">
      <q-breadcrumbs class="text-caption" active-color="secondary" gutter="xs">
        <q-breadcrumbs-el
          v-for="(level, i) in stack"
          :key="i"
          :label="level.label"
          :class="i < stack.length - 1 ? 'cursor-pointer' : 'text-grey-8'"
          @click="popTo(i)"
        />
      </q-breadcrumbs>
      <q-space />
      <span v-if="summary" class="text-caption text-grey-7">{{ summary }}</span>
      <q-badge
        v-if="benchmark?.placeholder"
        color="orange-7"
        :label="t('plots.placeholder')"
        class="q-ml-xs"
      />
    </div>
    <div v-if="error" class="text-negative text-caption">
      {{ t('plots.error') }}: {{ error }}
    </div>
    <div
      v-else-if="empty || (!loading && !year)"
      class="text-grey-7 text-caption"
    >
      {{ t('plots.no_data_for', { parameters: parameterLabel }) }}
    </div>
    <template v-else>
      <div :style="`height: ${height}px;`">
        <e-charts
          autoresize
          :init-options="initOptions"
          :option="option"
          :update-options="updateOptions"
          :loading="loading"
          @click="onClick"
        />
      </div>
      <q-markup-table
        v-if="points.length"
        flat
        dense
        class="trend-table q-mt-sm"
        :style="`height: ${tableHeight}px;`"
      >
        <thead>
          <tr>
            <th class="text-left">{{ current?.dimension.label }}</th>
            <th class="text-right">{{ t('plots.p50') }}</th>
            <th class="text-right">{{ t('plots.iqr') }}</th>
            <th class="text-right">{{ t('plots.days') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="point in points" :key="point.key">
            <td class="text-left">{{ point.label }}</td>
            <td class="text-right">{{ formatValue(point.stats.p50) }}</td>
            <td class="text-right">
              {{ formatValue(point.stats.p25) }} –
              {{ formatValue(point.stats.p75) }}
            </td>
            <td class="text-right">{{ point.n }}</td>
          </tr>
        </tbody>
      </q-markup-table>
    </template>
  </div>
</template>

<script setup lang="ts">
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import {
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
} from 'echarts/components';
import {
  benchmarkOf,
  initOptions,
  onBucketClick,
  roundBound,
  updateOptions,
} from '@/components/plots/charts';
import { useExploreRequest } from '@/composables/useExploreQuery';
import { useContextScope } from '@/composables/useContextScope';
import type {
  ExploreBucket,
  ExploreDimension,
  ExploreParams,
  ExploreStats,
} from '@/models';

use([
  SVGRenderer,
  LineChart,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
]);

interface Props {
  /** height of the plot area */
  height?: number;
  /** height of the table under the plot; it scrolls past it */
  tableHeight?: number;
}

interface Level {
  params: ExploreParams;
  dimension: ExploreDimension;
  label: string;
}

interface Point {
  key: string;
  label: string;
  n: number;
  stats: ExploreStats;
  bucket: ExploreBucket;
}

withDefaults(defineProps<Props>(), { height: 400, tableHeight: 200 });
const { t, locale } = useI18n();
const router = useRouter();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const MEDIAN_COLOR = '#2f5596';
const BAND_COLOR = 'rgba(79, 143, 204, 0.18)';
const BENCHMARK_COLOR = '#d32f2f';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';

const {
  parameter,
  parameterOptions,
  parameterLabel,
  context,
  contextValue,
  contextOptions,
  contextLabel,
  valueOptions,
  valuesLoading,
  scopedFilter,
  refresh,
  selectParameter,
  selectContext,
  selectValue,
} = useContextScope();
const year = ref<number | null>(null);
/** Drill stack: the year by month, then a month by day. */
const stack = ref<Level[]>([]);
const current = computed(() => stack.value[stack.value.length - 1] ?? null);
const option = ref<EChartsOption>({});
/** every period of the level, gaps included, null where no data */
const slots = ref<{ key: string; label: string; point: Point | null }[]>([]);

const trendRequest = useExploreRequest('measurements');
const yearsRequest = useExploreRequest('measurements');
const { result, loading, error, empty } = trendRequest;

const points = computed(() =>
  slots.value.flatMap((slot) => (slot.point ? [slot.point] : [])),
);

const yearOptions = computed(() =>
  (yearsRequest.result.value?.buckets || [])
    .flatMap((b) => (b.key[0] ? [new Date(b.key[0]).getUTCFullYear()] : []))
    .sort((a, b) => b - a)
    .map((y) => ({ value: y, label: String(y) })),
);

const benchmark = computed(() =>
  benchmarkOf(exploreStore.schema, parameter.value),
);

const unit = computed(() => result.value?.meta.unit || '');

function formatValue(value: number): string {
  return new Intl.NumberFormat(locale.value, {
    maximumFractionDigits: value < 10 ? 2 : 0,
  }).format(value);
}

/** the year's (or month's) highest and lowest median */
const summary = computed(() => {
  const items = points.value;
  if (!items.length) return '';
  const u = unit.value ? ` ${unit.value}` : '';
  const peak = items.reduce((a, b) => (b.stats.p50 > a.stats.p50 ? b : a));
  const low = items.reduce((a, b) => (b.stats.p50 < a.stats.p50 ? b : a));
  return [
    t('plots.peak', {
      value: `${formatValue(peak.stats.p50)}${u}`,
      period: peak.label,
    }),
    t('plots.low', {
      value: `${formatValue(low.stats.p50)}${u}`,
      period: low.label,
    }),
  ].join(' · ');
});

/**
 * Years with data for the pollutant and context, then the trend: keeps the
 * year if still offered, else picks the one with the most days.
 */
async function reload(): Promise<void> {
  if (!parameter.value) {
    year.value = null;
    return restart();
  }
  const value = await yearsRequest.load({
    ...scopedFilter(),
    agg: 'count',
    by: ['year'],
    parameters: [parameter.value],
    grain: 'day',
  });
  if (!value) return;
  const years = value.buckets.flatMap((b) =>
    b.key[0] ? [{ year: new Date(b.key[0]).getUTCFullYear(), n: b.n }] : [],
  );
  if (year.value === null || !years.some((y) => y.year === year.value)) {
    const busiest = years.reduce<{ year: number; n: number } | null>(
      (best, y) => (!best || y.n > best.n ? y : best),
      null,
    );
    year.value = busiest?.year ?? null;
  }
  return restart();
}

/** Settle the menus, then reload: on mount and when the filters are applied. */
async function refreshAll(): Promise<void> {
  await refresh();
  await reload();
}

async function onParameter(value: string | null): Promise<void> {
  await selectParameter(value);
  await reload();
}

function onYear(value: number | null): void {
  year.value = value;
  void restart();
}

async function onContext(value: string | null): Promise<void> {
  // the trend changes only if a value of the old context was narrowing it
  const narrowed = contextValue.value !== null;
  await selectContext(value);
  if (narrowed) await reload();
}

function onValue(value: string | null): void {
  selectValue(value);
  void reload();
}

onMounted(() => void refreshAll());
// applying the filters restarts the drill from the top
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refreshAll());
});

/** Rebuild the year level and load it. */
function restart(): Promise<void> {
  const dimension = exploreStore.dimension('month');
  if (!dimension || !parameter.value || year.value === null) return show([]);
  const params: ExploreParams = {
    ...scopedFilter(),
    agg: 'stats',
    by: ['month'],
    parameters: [parameter.value],
    grain: 'day',
    from: `${year.value}-01-01`,
    to: `${year.value + 1}-01-01`,
  };
  return show([{ params, dimension, label: String(year.value) }]);
}

/** Make `levels` the drill stack and load its last level. */
async function show(levels: Level[]): Promise<void> {
  stack.value = levels;
  const level = current.value;
  const value = await trendRequest.load(level?.params ?? null);
  // a later show() took over while this one waited
  if (current.value !== level) return;
  if (!value || !level) {
    slots.value = [];
    option.value = {};
    return;
  }
  const byKey = new Map(
    value.buckets.flatMap((b) =>
      b.key[0] && b.stats ? [[periodKey(b.key[0]), b] as const] : [],
    ),
  );
  slots.value = periods(level).map(({ key, label }) => {
    const bucket = byKey.get(key);
    return {
      key,
      label,
      point: bucket?.stats
        ? { key, label, n: bucket.n, stats: bucket.stats, bucket }
        : null,
    };
  });
  option.value = buildOption();
}

/** yyyy-mm-dd of a bucket key, whatever time part the server adds */
function periodKey(key: string): string {
  return key.substring(0, 10);
}

/** every month of the year, or every day of the month, in order */
function periods(level: Level): { key: string; label: string }[] {
  const start = new Date(`${level.params.from}T00:00:00Z`);
  const end = new Date(`${level.params.to}T00:00:00Z`);
  const byMonth = level.dimension.key === 'month';
  const format = new Intl.DateTimeFormat(
    locale.value,
    byMonth
      ? { month: 'short', timeZone: 'UTC' }
      : { day: 'numeric', timeZone: 'UTC' },
  );
  const out: { key: string; label: string }[] = [];
  for (const date = new Date(start); date < end;) {
    out.push({
      key: date.toISOString().substring(0, 10),
      label: format.format(date),
    });
    if (byMonth) date.setUTCMonth(date.getUTCMonth() + 1);
    else date.setUTCDate(date.getUTCDate() + 1);
  }
  return out;
}

function buildOption(): EChartsOption {
  const b = benchmark.value;
  const u = unit.value ? ` ${unit.value}` : '';
  const byMonth = current.value?.dimension.key === 'month';
  const medianName = byMonth
    ? t('plots.monthly_median')
    : t('plots.daily_median');
  const bandName = t('plots.iqr');
  const benchmarkName = b
    ? `${formatValue(b.value)} ${b.unit} ${b.note || b.source}`
    : '';
  const values = slots.value.map((slot) => slot.point?.stats ?? null);
  return {
    legend: {
      bottom: 0,
      itemWidth: 14,
      itemHeight: 10,
      itemGap: 24,
      textStyle: { color: TEXT },
      selectedMode: false,
      data: [
        { name: medianName, icon: 'circle' },
        { name: bandName, icon: 'rect' },
        ...(b
          ? [{ name: benchmarkName, icon: 'path://M0,4 L14,4 L14,6 L0,6 Z' }]
          : []),
      ],
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const first = Array.isArray(params) ? params[0] : params;
        const slot = first ? slots.value[first.dataIndex] : undefined;
        if (!slot?.point) return '';
        const s = slot.point.stats;
        return [
          `<b>${slot.label}</b>`,
          `${medianName}: <b>${formatValue(s.p50)}${u}</b>`,
          `${bandName}: ${formatValue(s.p25)} – ${formatValue(s.p75)}${u}`,
          `${t('plots.days')}: ${slot.point.n}`,
        ].join('<br/>');
      },
    },
    grid: { left: 8, right: 24, top: 16, bottom: 40, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: slots.value.map((slot) => slot.label),
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel: { color: TEXT },
    },
    yAxis: {
      type: 'value',
      scale: true,
      name: `${parameterLabel.value}${u ? ` (${unit.value})` : ''}`,
      nameLocation: 'middle',
      nameGap: 44,
      nameTextStyle: { color: MUTED },
      // keep the benchmark in view, bounds rounded to half a magnitude
      min: (extent: { min: number }) =>
        roundBound(Math.min(extent.min, b?.value ?? extent.min), Math.floor),
      max: (extent: { max: number }) =>
        roundBound(Math.max(extent.max, b?.value ?? extent.max), Math.ceil),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: [
      // the IQR band: p25 as an invisible base, p75 − p25 stacked on it
      {
        type: 'line',
        name: 'p25',
        stack: 'iqr',
        data: values.map((s) => s?.p25 ?? '-'),
        lineStyle: { opacity: 0 },
        symbol: 'none',
        silent: true,
      },
      {
        type: 'line',
        name: bandName,
        stack: 'iqr',
        data: values.map((s) => (s ? s.p75 - s.p25 : '-')),
        lineStyle: { opacity: 0 },
        areaStyle: { color: BAND_COLOR },
        itemStyle: { color: BAND_COLOR },
        symbol: 'none',
        silent: true,
      },
      {
        type: 'line',
        name: medianName,
        data: values.map((s) => s?.p50 ?? '-'),
        symbol: 'circle',
        symbolSize: 7,
        cursor: byMonth ? 'pointer' : 'default',
        lineStyle: { color: MEDIAN_COLOR, width: 2.5 },
        itemStyle: { color: MEDIAN_COLOR },
        ...(b
          ? {
              markLine: {
                silent: true,
                symbol: 'none',
                lineStyle: {
                  color: BENCHMARK_COLOR,
                  type: 'dashed',
                  width: 1.5,
                },
                label: { show: false },
                data: [{ yAxis: b.value }],
              },
            }
          : {}),
      },
      // legend swatch for the benchmark line
      ...(b
        ? [
            {
              type: 'line' as const,
              name: benchmarkName,
              data: [],
              itemStyle: { color: BENCHMARK_COLOR },
            },
          ]
        : []),
    ],
  };
}

/** a click on a month drills into its days */
function onClick(event: { dataIndex?: number; seriesName?: string }) {
  const level = current.value;
  if (!level?.dimension.drill_to || level.dimension.key !== 'month') return;
  const slot =
    event.dataIndex === undefined ? undefined : slots.value[event.dataIndex];
  if (!slot?.point) return;
  const next = onBucketClick(
    { kind: 'drill', dimension: level.dimension, params: level.params, router },
    { ...slot.point.bucket, key: [slot.key] },
  );
  const dimension = exploreStore.dimension(next?.by?.[0] || '');
  if (!next || !dimension) return;
  void show([
    ...stack.value,
    { params: next, dimension, label: `${slot.label} ${year.value}` },
  ]);
}

function popTo(index: number) {
  if (index < stack.value.length - 1)
    void show(stack.value.slice(0, index + 1));
}
</script>

<style scoped>
/* the table scrolls under its header, so the card keeps its height */
.trend-table :deep(thead tr th) {
  position: sticky;
  top: 0;
  z-index: 1;
  background: white;
}
</style>
