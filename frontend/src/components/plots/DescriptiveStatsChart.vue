<template>
  <div>
    <div class="row items-center q-col-gutter-sm q-mb-sm">
      <div class="col-6">
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
      <div class="col-6">
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
    </div>
    <div v-if="error" class="text-negative text-caption">
      {{ t('plots.error') }}: {{ error }}
    </div>
    <div v-else-if="empty" class="text-grey-7 text-caption">
      {{
        parameter
          ? t('plots.no_data_for', {
              parameters: exploreStore.parameterLabel(parameter),
            })
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
        @click="onClick"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import ECharts from 'vue-echarts';
import type { CustomSeriesRenderItem, EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { CustomChart, ScatterChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components';
import {
  initOptions,
  keyLabel,
  onBucketClick,
  STATS_CONTEXTS,
  updateOptions,
} from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';
import { DEFAULT_PARAMETER } from '@/stores/explore';
import type {
  ExploreBucket,
  ExploreDimension,
  ExploreParams,
  ExploreResult,
  ExploreStats,
} from '@/models';

use([
  SVGRenderer,
  CustomChart,
  ScatterChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
]);

interface Props {
  /** height of the plot area; the rows share it */
  height?: number;
}

interface Level {
  params: ExploreParams;
  dimension: ExploreDimension;
  label: string;
}

interface Row {
  name: string;
  stats: ExploreStats;
  bucket: ExploreBucket;
}

withDefaults(defineProps<Props>(), { height: 400 });
const { t, locale } = useI18n();
const router = useRouter();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const RANGE_COLOR = '#bdbdbd';
const PERCENTILE_COLOR = '#2f5596';
const MEAN_COLOR = '#d32f2f';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';
const PERCENTILES = ['p05', 'p25', 'p50', 'p75', 'p95'] as const;

/** the pollutant compared; stats take one at a time */
const parameter = ref<string | null>(null);
const context = ref('country');
/** Drill stack, `stack[0]` being the chosen context. */
const stack = ref<Level[]>([]);
const current = computed(() => stack.value[stack.value.length - 1] ?? null);
const option = ref<EChartsOption>({});
const rows = ref<Row[]>([]);

const { result, loading, error, empty, load } =
  useExploreRequest('measurements');

/** the selected pollutants, or every pollutant when none is selected */
const parameterOptions = computed(() => {
  const selected = new Set(exploreStore.parameters);
  return exploreStore.parameterOptions.filter(
    (opt) => !selected.size || selected.has(opt.value),
  );
});

const contextOptions = computed(() =>
  STATS_CONTEXTS.flatMap((key) => {
    const dimension = exploreStore.dimension(key);
    return dimension ? [{ value: key, label: dimension.label }] : [];
  }),
);

const unit = computed(() => result.value?.meta.unit || '');

function formatValue(value: number): string {
  return new Intl.NumberFormat(locale.value, {
    maximumFractionDigits: value < 10 ? 2 : 0,
  }).format(value);
}

function formatCount(value: number): string {
  return value.toLocaleString(locale.value);
}

const summary = computed(() => {
  const value = result.value;
  if (!value || value.meta.n === 0 || !rows.value.length) return '';
  return `${formatCount(value.meta.n_records ?? 0)} ${t('plots.records').toLowerCase()} · ${t(
    'plots.daily_means',
  )}`;
});

/**
 * The pollutant menu follows the global selection: keeps the choice while
 * offered, else the default, else the first.
 */
function settleParameter(): void {
  const values = parameterOptions.value.map((opt) => opt.value);
  if (parameter.value && values.includes(parameter.value)) return;
  parameter.value = values.includes(DEFAULT_PARAMETER)
    ? DEFAULT_PARAMETER
    : (values[0] ?? null);
}

/** Settle the pollutant, then restart the drill: on mount and when the filters are applied. */
function refresh(): Promise<void> {
  settleParameter();
  return restart();
}

function onParameter(value: string | null): void {
  parameter.value = value;
  void restart();
}

function onContext(value: string): void {
  context.value = value;
  void restart();
}

onMounted(() => void refresh());
// applying the filters restarts the drill from the top
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refresh());
});

/** Rebuild the first level from the current filters and load it. */
function restart(): Promise<void> {
  const dimension = exploreStore.dimension(context.value);
  if (!dimension || !parameter.value) return show([]);
  const params: ExploreParams = {
    agg: 'stats',
    by: [context.value],
    parameters: [parameter.value],
    grain: 'day',
    filter: exploreFilter(),
    ...exploreRange(),
  };
  return show([{ params, dimension, label: dimension.label }]);
}

/** Make `levels` the drill stack and load its last level. */
async function show(levels: Level[]): Promise<void> {
  stack.value = levels;
  const level = current.value;
  const value = await load(level?.params ?? null);
  // a later show() took over while this one waited
  if (current.value !== level) return;
  if (!value || !level) {
    rows.value = [];
    option.value = {};
    return;
  }
  rows.value = toRows(level, value);
  option.value = buildOption(rows.value);
}

/** one row per key with stats, highest median at the top */
function toRows(level: Level, value: ExploreResult): Row[] {
  return value.buckets
    .flatMap((bucket) => {
      const key = bucket.key[0];
      if (!bucket.stats) return [];
      return [
        {
          name:
            key === null || key === undefined
              ? t('plots.unknown')
              : keyLabel(level.dimension.key, key),
          stats: bucket.stats,
          bucket,
        },
      ];
    })
    .sort((a, b) => a.stats.p50 - b.stats.p50);
}

/** the grey observed range, min to max, as a thin line */
const renderRange: CustomSeriesRenderItem = (_params, api) => {
  const [x0 = 0, y = 0] = api.coord([api.value(1), api.value(0)]);
  const [x1 = 0] = api.coord([api.value(2), api.value(0)]);
  return {
    type: 'line',
    shape: { x1: x0, y1: y, x2: x1, y2: y },
    style: { stroke: RANGE_COLOR, lineWidth: 2 },
  };
};

function buildOption(items: Row[]): EChartsOption {
  const names = items.map((row) => row.name);
  const rangeName = t('plots.observed_range');
  const percentileName = t('plots.percentile_landmarks');
  const meanName = t('plots.mean');
  return {
    legend: {
      bottom: 0,
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 24,
      textStyle: { color: TEXT },
      data: [
        { name: percentileName },
        { name: rangeName },
        { name: meanName, icon: 'triangle' },
      ],
      selectedMode: false,
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const first = Array.isArray(params) ? params[0] : params;
        const row = first ? items[first.dataIndex] : undefined;
        if (!row) return '';
        const s = row.stats;
        const u = unit.value ? ` ${unit.value}` : '';
        const line = (label: string, value: number) =>
          `${label}: <b>${formatValue(value)}${u}</b>`;
        return [
          `<b>${row.name}</b>`,
          line(t('plots.mean'), s.mean),
          ...(s.sd === undefined ? [] : [line(t('plots.sd'), s.sd)]),
          line(t('plots.min'), s.min),
          ...PERCENTILES.map((p) => line(t(`plots.${p}`), s[p])),
          line(t('plots.max'), s.max),
          `${t('plots.days')}: ${formatCount(row.bucket.n)}`,
        ].join('<br/>');
      },
    },
    grid: { left: 8, right: 24, top: 8, bottom: 40, containLabel: true },
    xAxis: {
      type: 'value',
      scale: true,
      name: unit.value
        ? `${exploreStore.parameterLabel(parameter.value || '')} (${unit.value})`
        : exploreStore.parameterLabel(parameter.value || ''),
      nameLocation: 'middle',
      nameGap: 28,
      nameTextStyle: { color: MUTED },
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel: { color: MUTED },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: TEXT, width: 140, overflow: 'truncate' },
      triggerEvent: true,
    },
    series: [
      {
        type: 'custom',
        name: rangeName,
        renderItem: renderRange,
        encode: { x: [1, 2], y: 0 },
        data: items.map((row, i) => [i, row.stats.min, row.stats.max]),
        itemStyle: { color: RANGE_COLOR },
        silent: true,
        z: 1,
      },
      {
        type: 'scatter',
        name: rangeName,
        symbolSize: 8,
        itemStyle: { color: RANGE_COLOR },
        data: items.flatMap((row) => [
          [row.stats.min, row.name],
          [row.stats.max, row.name],
        ]),
        silent: true,
        z: 2,
      },
      {
        type: 'scatter',
        name: percentileName,
        symbolSize: 9,
        itemStyle: { color: PERCENTILE_COLOR },
        data: items.flatMap((row) =>
          PERCENTILES.map((p) => [row.stats[p], row.name]),
        ),
        cursor: clickable.value ? 'pointer' : 'default',
        z: 3,
      },
      {
        type: 'scatter',
        name: meanName,
        symbol: 'triangle',
        symbolSize: 11,
        itemStyle: { color: MEAN_COLOR },
        data: items.map((row) => [row.stats.mean, row.name]),
        cursor: clickable.value ? 'pointer' : 'default',
        z: 4,
      },
    ],
  };
}

const clickable = computed(() => !!current.value?.dimension.drill_to);

/** a click on a row, its markers or its label drills into it */
function onClick(event: {
  componentType?: string;
  value?: unknown;
  data?: unknown;
}) {
  const level = current.value;
  if (!level || !clickable.value) return;
  const name =
    event.componentType === 'yAxis'
      ? (event.value as string)
      : (event.data as [number, string] | undefined)?.[1];
  const row = rows.value.find((r) => r.name === name);
  if (!row) return;
  const next = onBucketClick(
    {
      kind: 'drill',
      dimension: level.dimension,
      params: level.params,
      router,
    },
    row.bucket,
  );
  if (!next) return;
  const dimension = exploreStore.dimension(next.by?.[0] || '');
  if (!dimension) return;
  void show([...stack.value, { params: next, dimension, label: row.name }]);
}

function popTo(index: number) {
  if (index < stack.value.length - 1)
    void show(stack.value.slice(0, index + 1));
}
</script>
