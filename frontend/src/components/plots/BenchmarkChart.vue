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
      <span v-if="benchmarkLabel" class="text-caption text-grey-7">
        {{ benchmarkLabel }}
        <q-badge
          v-if="benchmark?.placeholder"
          color="orange-7"
          :label="t('plots.placeholder')"
          class="q-ml-xs"
        />
      </span>
    </div>
    <div v-if="error" class="text-negative text-caption">
      {{ t('plots.error') }}: {{ error }}
    </div>
    <div v-else-if="skipped || empty" class="text-grey-7 text-caption">
      {{ noDataMessage }}
    </div>
    <template v-else>
      <div v-if="partialError" class="text-grey-7 text-caption">
        {{ t('plots.partial_error') }}: {{ partialError }}
      </div>
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
    </template>
  </div>
</template>

<script setup lang="ts">
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { ScatterChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import {
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
} from 'echarts/components';
import {
  benchmarkOf,
  clickedRow,
  initOptions,
  keyLabel,
  refine,
  roundBound,
  updateOptions,
} from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useDrillStack } from '@/composables/useDrillStack';
import { useExploreRequest } from '@/composables/useExploreQuery';
import {
  useContextChoice,
  useParameterChoice,
} from '@/composables/useContextScope';
import type {
  ExploreBucket,
  ExploreDimension,
  ExploreParams,
  ExploreResult,
} from '@/models';

use([
  SVGRenderer,
  ScatterChart,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
]);

interface Props {
  /** height of the plot area; the rows share it */
  height?: number;
}

/** One drill level: the same context, three requests. */
interface Level {
  /** distribution under the global filters */
  filtered: ExploreParams;
  /** distribution over the whole database */
  database: ExploreParams;
  /** share of periods above the benchmark, under the global filters */
  exceedance: ExploreParams;
  dimension: ExploreDimension;
  label: string;
}

/** A level's answers: the database medians and the shares may be missing. */
interface Loaded {
  filtered: ExploreResult;
  database: ExploreResult | null;
  exceedance: ExploreResult | null;
}

interface Row {
  key: string | null;
  name: string;
  median: number;
  databaseMedian: number | null;
  /** share of periods at or below the benchmark, 0..1 */
  below: number | null;
  bucket: ExploreBucket;
}

withDefaults(defineProps<Props>(), { height: 400 });
const { t } = useI18n();
const { formatValue, formatShare, describeBenchmark } = useChartFormat();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const FILTERED_COLOR = '#2f5596';
const DATABASE_COLOR = '#9e9e9e';
const BENCHMARK_COLOR = '#d32f2f';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';

const parameters = useParameterChoice({
  withBenchmark: true,
});
const { parameter, parameterOptions, parameterLabel, noDataMessage } =
  parameters;
const contexts = useContextChoice(parameter);
const { context, contextOptions, contextDimension } = contexts;
const option = ref<EChartsOption>({});
const rows = ref<Row[]>([]);

const filteredRequest = useExploreRequest('measurements');
const databaseRequest = useExploreRequest('measurements');
const exceedanceRequest = useExploreRequest('measurements');
const { result, empty, skipped } = filteredRequest;
/** `stack[0]` is the chosen context */
const { stack, current, show, popTo } = useDrillStack<Level, Loaded>({
  fetch: loadLevel,
  paint: (level, loaded) => {
    rows.value = toRows(level, loaded);
    option.value = buildOption(rows.value);
  },
  clear: () => {
    rows.value = [];
    option.value = {};
  },
});
const loading = computed(
  () =>
    filteredRequest.loading.value ||
    databaseRequest.loading.value ||
    exceedanceRequest.loading.value,
);
/** the chart stands on the filtered medians alone */
const error = computed(() => filteredRequest.error.value);
/** the database medians and the shares only add to it: missing, the rows show without them */
const partialError = computed(
  () => databaseRequest.error.value || exceedanceRequest.error.value,
);

const benchmark = computed(() =>
  benchmarkOf(exploreStore.schema, parameter.value),
);

const unit = computed(
  () => result.value?.meta.unit || benchmark.value?.unit || '',
);

const benchmarkLabel = computed(() =>
  benchmark.value ? describeBenchmark(benchmark.value) : '',
);

/** Settle the menus, then restart the drill: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  await parameters.refresh();
  await contexts.refresh();
  await restart();
}

async function onParameter(value: string | null): Promise<void> {
  parameter.value = value;
  await contexts.refresh();
  await restart();
}

function onContext(value: string | null): void {
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
  const dimension = contextDimension.value;
  const b = benchmark.value;
  if (!dimension || !parameter.value || !b) return show([]);
  // the benchmark's averaging period sets the grain of both statistics
  const base: ExploreParams = {
    by: [dimension.key],
    parameters: [parameter.value],
    grain: b.averaging,
  };
  const scoped = { filter: exploreFilter(), ...exploreRange() };
  return show([
    {
      filtered: { ...base, ...scoped, agg: 'stats' },
      database: { ...base, agg: 'stats' },
      exceedance: { ...base, ...scoped, agg: 'exceedance', threshold: b.value },
      dimension,
      label: dimension.label,
    },
  ]);
}

/** The level's three requests; only the filtered one is required. */
async function loadLevel(level: Level | null): Promise<Loaded | null> {
  const [filtered, database, exceedance] = await Promise.all([
    filteredRequest.load(level?.filtered ?? null),
    databaseRequest.load(level?.database ?? null),
    exceedanceRequest.load(level?.exceedance ?? null),
  ]);
  return filtered ? { filtered, database, exceedance } : null;
}

/** one row per key with stats, highest median at the top */
function toRows(
  level: Level,
  { filtered, database, exceedance }: Loaded,
): Row[] {
  const medians = new Map(
    (database?.buckets || []).map((b) => [b.key[0] ?? null, b.stats?.p50]),
  );
  const shares = new Map(
    (exceedance?.buckets || []).map((b) => [
      b.key[0] ?? null,
      b.exceedance?.share,
    ]),
  );
  return filtered.buckets
    .flatMap((bucket) => {
      const key = bucket.key[0] ?? null;
      if (!bucket.stats) return [];
      const share = shares.get(key);
      return [
        {
          key,
          name:
            key === null
              ? t('plots.unknown')
              : keyLabel(level.dimension.key, key),
          median: bucket.stats.p50,
          databaseMedian: medians.get(key) ?? null,
          below: share === undefined ? null : 1 - share,
          bucket,
        },
      ];
    })
    .sort((a, b) => a.median - b.median);
}

function buildOption(items: Row[]): EChartsOption {
  const b = benchmark.value;
  const names = items.map((row) => row.name);
  const filteredName = t('plots.datasets_filtered');
  const databaseName = t('plots.database_median');
  const benchmarkName = b?.placeholder
    ? `${t('plots.benchmark')} (${t('plots.placeholder').toLowerCase()})`
    : (b?.source ?? t('plots.benchmark'));
  const u = unit.value ? ` ${unit.value}` : '';
  const clickable = !!current.value?.dimension.drill_to;
  return {
    legend: {
      bottom: 0,
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 24,
      textStyle: { color: TEXT },
      selectedMode: false,
      data: [
        { name: filteredName, icon: 'circle' },
        { name: databaseName, icon: 'diamond' },
        { name: benchmarkName, icon: 'triangle' },
      ],
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const first = Array.isArray(params) ? params[0] : params;
        const row = first ? items[first.dataIndex] : undefined;
        if (!row) return '';
        return [
          `<b>${row.name}</b>`,
          `${filteredName}: <b>${formatValue(row.median)}${u}</b>`,
          ...(row.databaseMedian === null
            ? []
            : [`${databaseName}: ${formatValue(row.databaseMedian)}${u}`]),
          ...(b ? [`${benchmarkName}: ${formatValue(b.value)}${u}`] : []),
          ...(row.below === null
            ? []
            : [t('plots.below_benchmark', { share: formatShare(row.below) })]),
        ].join('<br/>');
      },
    },
    grid: { left: 8, right: 8, top: 36, bottom: 64, containLabel: true },
    xAxis: {
      type: 'value',
      position: 'top',
      name: `${parameterLabel.value}${unit.value ? ` (${unit.value})` : ''}`,
      nameLocation: 'middle',
      nameGap: 24,
      nameTextStyle: { color: MUTED },
      min: 0,
      // keep the benchmark in view even when every median is far below it
      max: (extent: { max: number }) =>
        roundBound(Math.max(extent.max, b?.value ?? 0) * 1.1, Math.ceil),
      axisLine: { show: false },
      axisTick: { show: false },
      // the last tick would run into the share column's header
      axisLabel: { color: MUTED, showMaxLabel: false },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    yAxis: [
      {
        type: 'category',
        data: names,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: TEXT, width: 140, overflow: 'truncate' },
        triggerEvent: true,
      },
      // the share below the benchmark, as a column on the right
      {
        type: 'category',
        position: 'right',
        data: names,
        name: t('plots.below_benchmark_short'),
        nameLocation: 'end',
        nameTextStyle: { color: MUTED, align: 'right' },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: TEXT,
          formatter: (_value: string, index: number) => {
            const below = items[index]?.below;
            return below === null || below === undefined
              ? '–'
              : formatShare(below);
          },
        },
      },
    ],
    series: [
      {
        type: 'scatter',
        name: databaseName,
        symbol: 'diamond',
        symbolSize: 16,
        // hollow and on top, so it stays visible over an equal filtered median
        itemStyle: {
          color: 'transparent',
          borderColor: DATABASE_COLOR,
          borderWidth: 2,
        },
        // a number on the category axis is the row index: labels repeat
        data: items.map((row, i) => [row.databaseMedian ?? '-', i]),
        cursor: clickable ? 'pointer' : 'default',
        z: 4,
      },
      {
        type: 'scatter',
        name: filteredName,
        symbolSize: 12,
        itemStyle: { color: FILTERED_COLOR },
        data: items.map((row, i) => [row.median, i]),
        cursor: clickable ? 'pointer' : 'default',
        z: 3,
      },
      {
        // carries the benchmark line; the legend entry is its own
        type: 'scatter',
        name: benchmarkName,
        symbol: 'triangle',
        itemStyle: { color: BENCHMARK_COLOR },
        data: [],
        ...(b
          ? {
              markLine: {
                silent: true,
                symbol: ['none', 'triangle'],
                symbolRotate: 180,
                symbolSize: 12,
                lineStyle: {
                  color: BENCHMARK_COLOR,
                  type: 'dashed',
                  width: 1.5,
                },
                label: {
                  show: true,
                  // the top belongs to the axis labels
                  position: 'start',
                  color: BENCHMARK_COLOR,
                  formatter: formatValue(b.value),
                },
                data: [{ xAxis: b.value }],
              },
            }
          : {}),
      },
    ],
  };
}

/** a click on a row's markers or its label drills into it */
function onClick(event: Parameters<typeof clickedRow>[0]) {
  const level = current.value;
  const drillTo = level?.dimension.drill_to;
  if (!level || !drillTo) return;
  const index = clickedRow(event);
  const row = index === undefined ? undefined : rows.value[index];
  if (!row || row.key === null) return;
  const key = row.key;
  const next = (params: ExploreParams): ExploreParams => ({
    ...refine(params, level.dimension, key),
    by: [drillTo],
  });
  const dimension = exploreStore.dimension(drillTo);
  if (!dimension) return;
  void show([
    ...stack.value,
    {
      filtered: next(level.filtered),
      database: next(level.database),
      exceedance: next(level.exceedance),
      dimension,
      label: row.name,
    },
  ]);
}
</script>
