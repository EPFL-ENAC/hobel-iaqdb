<template>
  <div ref="root">
    <div class="row items-center q-col-gutter-sm q-mb-sm">
      <div class="col-6">
        <q-select
          :model-value="x"
          :options="xOptions"
          :label="t('plots.x_variable')"
          :loading="coverage.loading.value"
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onX"
        />
      </div>
      <div class="col-6">
        <q-select
          :model-value="y"
          :options="yOptions"
          :label="t('plots.y_variable')"
          :loading="probing"
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onY"
        />
      </div>
    </div>
    <div class="row items-center no-wrap q-mb-xs">
      <span class="text-caption text-grey-8">{{ grainLabel }}</span>
      <q-space />
      <span v-if="summary" class="text-caption text-grey-7">{{ summary }}</span>
    </div>
    <div v-if="error" class="text-negative text-caption">
      {{ t('plots.error') }}: {{ error }}
    </div>
    <div v-else-if="!probing && (!x || !y)" class="text-grey-7 text-caption">
      {{ t('plots.no_pairs_for', { parameter: label(x) }) }}
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
import { LineChart, ScatterChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components';
import { initOptions, updateOptions } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useExploreRequest } from '@/composables/useExploreQuery';
import { useParametersWithRecords } from '@/composables/useContextScope';
import type { ExploreParams } from '@/models';

use([
  SVGRenderer,
  ScatterChart,
  LineChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
]);

interface Props {
  /** height of the plot area */
  height?: number;
}

withDefaults(defineProps<Props>(), { height: 400 });
const { t, locale } = useI18n();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();
const { formatValue } = useChartFormat();

/** the pair the chart opens on, when both have data together */
const DEFAULT_X = 'air_temperature';
const DEFAULT_Y = 'co2';
const POINT_COLOR = 'rgba(47, 85, 150, 0.45)';
const FIT_COLOR = '#d32f2f';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';

const root = ref<HTMLElement | null>(null);
const x = ref<string | null>(null);
const y = ref<string | null>(null);
/** pollutants measured together with x */
const partners = ref<Set<string>>(new Set());

const coverage = useParametersWithRecords();
const probe = useExploreRequest('relationships');
const probing = probe.loading;
const { result, loading, error, load } = useExploreRequest('relationships');

/** every pollutant with records under the filters */
const xOptions = coverage.options;

/** the pollutants measured in the same space and hour as x */
const yOptions = computed(() =>
  xOptions.value.filter((opt) => partners.value.has(opt.value)),
);

function label(slug: string | null): string {
  if (!slug) return '';
  return (
    exploreStore.parameterOptions.find((opt) => opt.value === slug)?.label ||
    slug
  );
}

const grainLabel = computed(() =>
  result.value?.meta.grain === 'hour' ? t('plots.paired_hours') : '',
);

/** "weak negative trend": the strength by |r|, the direction by its sign */
function trendLabel(r: number): string {
  const size = Math.abs(r);
  if (size < 0.1) return t('plots.trend_none');
  const strength =
    size < 0.3
      ? t('plots.trend_weak')
      : size < 0.5
        ? t('plots.trend_moderate')
        : t('plots.trend_strong');
  const direction =
    r < 0 ? t('plots.trend_negative') : t('plots.trend_positive');
  return t('plots.trend_label', { strength, direction });
}

const summary = computed(() => {
  const bucket = result.value?.buckets[0];
  const r = bucket?.fit?.r;
  if (!bucket?.n || r === undefined) return '';
  const parts = [
    trendLabel(r),
    `r = ${r.toFixed(2)}`,
    t('plots.paired_hours_count', {
      count: bucket.n.toLocaleString(locale.value),
    }),
  ];
  if (bucket.sampled) parts.push(t('plots.sampled'));
  return parts.join(' · ');
});

const option = computed<EChartsOption>(() => {
  const bucket = result.value?.buckets[0];
  const points = bucket?.points || [];
  if (!bucket || !points.length) return {};
  const xs = points.map(([px]) => px);
  const ys = points.map(([, py]) => py);
  const lo = Math.min(...xs);
  const hi = Math.max(...xs);
  const fit = bucket.fit;
  const line =
    fit?.slope !== undefined && fit.intercept !== undefined
      ? [
          [lo, fit.slope * lo + fit.intercept],
          [hi, fit.slope * hi + fit.intercept],
        ]
      : [];
  const xName = label(x.value);
  const yName = label(y.value);
  const pointsName = t('plots.observations');
  const fitName = t('plots.trend_line');
  return {
    legend: {
      bottom: 0,
      itemWidth: 14,
      itemHeight: 10,
      itemGap: 24,
      textStyle: { color: TEXT },
      selectedMode: false,
      data: [
        { name: pointsName, icon: 'circle' },
        ...(line.length ? [{ name: fitName }] : []),
      ],
    },
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const item = Array.isArray(p) ? p[0] : p;
        if (!item || item.seriesName !== pointsName) return '';
        const [px, py] = item.value as [number, number];
        return `${xName}: <b>${formatValue(px)}</b><br/>${yName}: <b>${formatValue(py)}</b>`;
      },
    },
    grid: { left: 16, right: 24, top: 36, bottom: 56, containLabel: true },
    xAxis: {
      type: 'value',
      scale: true,
      // concentrations stay on the positive side; the fit line is clipped
      ...(lo >= 0 ? { min: 0 } : {}),
      name: xName,
      nameLocation: 'middle',
      nameGap: 28,
      nameTextStyle: { color: MUTED },
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel: { color: MUTED },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      ...(Math.min(...ys) >= 0 ? { min: 0 } : {}),
      name: yName,
      nameLocation: 'end',
      nameTextStyle: { color: MUTED, align: 'left' },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: [
      {
        type: 'scatter',
        name: pointsName,
        data: points,
        symbolSize: 5,
        itemStyle: { color: POINT_COLOR },
        cursor: 'default',
      },
      ...(line.length
        ? [
            {
              type: 'line' as const,
              name: fitName,
              data: line,
              symbol: 'none',
              silent: true,
              lineStyle: { color: FIT_COLOR, width: 2 },
              itemStyle: { color: FIT_COLOR },
            },
          ]
        : []),
    ],
  };
});

function scope(): Pick<ExploreParams, 'filter' | 'from' | 'to'> {
  return { filter: exploreFilter(), ...exploreRange() };
}

/** Pollutants with records; keeps x while offered, else the default, else the first. */
async function settleX(): Promise<void> {
  await coverage.refresh();
  const offered = xOptions.value.map((opt) => opt.value);
  if (x.value && offered.includes(x.value)) return;
  x.value = offered.includes(DEFAULT_X) ? DEFAULT_X : (offered[0] ?? null);
}

/**
 * Which pollutants were measured with x, those sharing hours with it in one
 * request. Then y: kept while offered, else the default, else the first.
 */
async function settleY(): Promise<void> {
  const value = await probe.load(
    x.value ? { agg: 'partners', x: x.value, ...scope() } : null,
  );
  partners.value = new Set(
    (value?.buckets || []).flatMap((b) => (b.n && b.key[0] ? [b.key[0]] : [])),
  );
  const offered = yOptions.value.map((opt) => opt.value);
  if (y.value && offered.includes(y.value)) return;
  y.value = offered.includes(DEFAULT_Y) ? DEFAULT_Y : (offered[0] ?? null);
}

function reload(): void {
  void load(
    x.value && y.value
      ? { agg: 'pairs', x: x.value, y: y.value, ...scope() }
      : null,
  );
}

/** Settle both menus, then load: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  await settleX();
  await settleY();
  reload();
}

async function onX(value: string | null): Promise<void> {
  x.value = value;
  await settleY();
  reload();
}

function onY(value: string | null): void {
  y.value = value;
  reload();
}

onMounted(() => void refresh());
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refresh());
});
// a correlation matrix cell opens its pair here
exploreStore.$onAction(({ name, args }) => {
  if (name !== 'showPair') return;
  const [px, py] = args;
  root.value?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  x.value = px;
  void settleY().then(() => {
    if (partners.value.has(py)) y.value = py;
    reload();
  });
});
</script>
