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
          :model-value="metric"
          :options="metricOptions"
          :label="t('plots.metric')"
          :loading="probing"
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onMetric"
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
    <div v-else-if="!probing && !metric" class="text-grey-7 text-caption">
      {{
        t('plots.no_pairs', {
          parameter: parameterLabel,
          metrics: probedMetrics,
        })
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
import { useParameterChoice } from '@/composables/useContextScope';
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
  /** catalog metric the chart opens on, when it has pairs */
  defaultMetric?: string;
}

const props = withDefaults(defineProps<Props>(), {
  height: 400,
  defaultMetric: 'space.occupancy_density',
});
const i18n = useI18n();
const { t, locale } = i18n;
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();
const { formatValue } = useChartFormat();

const POINT_COLOR = 'rgba(47, 85, 150, 0.55)';
const FIT_COLOR = '#d32f2f';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';

const parameters = useParameterChoice();
const { parameter, parameterOptions, parameterLabel } = parameters;
const metric = ref<string | null>(null);

/**
 * One pairs request per catalog metric; the menu lists those with pairs and
 * the chart draws the chosen one, so switching metric costs no request.
 */
const probes = new Map(
  (exploreStore.schema?.metrics || []).map(
    (key) => [key, useExploreRequest('relationships')] as const,
  ),
);
const current = computed(() =>
  metric.value ? probes.get(metric.value) : undefined,
);
const result = computed(() => current.value?.result.value ?? null);
const loading = computed(() => current.value?.loading.value ?? false);
/** the chosen metric's error; with no metric offered, the first probe's that failed */
const error = computed(() =>
  current.value
    ? current.value.error.value
    : ([...probes.values()].find((probe) => probe.error.value)?.error.value ??
      null),
);
const probing = computed(() =>
  [...probes.values()].some((probe) => probe.loading.value),
);

function metricName(key: string): string {
  const path = `plots.metrics.${key.replace('.', '_')}`;
  return i18n.te(path) ? t(path) : key;
}

/** metrics with at least one pair for the pollutant */
const metricOptions = computed(() =>
  [...probes.entries()].flatMap(([key, probe]) =>
    probe.result.value?.meta.n ? [{ value: key, label: metricName(key) }] : [],
  ),
);

/** the metrics probed, for the no-pairs note: "floor area or altitude (m)" */
const probedMetrics = computed(() =>
  new Intl.ListFormat(locale.value, { type: 'disjunction' }).format(
    [...probes.keys()].map((key) => metricName(key).toLowerCase()),
  ),
);

const metricLabel = computed(() =>
  metric.value ? metricName(metric.value) : '',
);

const unit = computed(() => result.value?.meta.unit || '');

const grainLabel = computed(() =>
  result.value?.meta.grain === 'space' ? t('plots.one_point_per_space') : '',
);

/** points, correlation and fit quality */
const summary = computed(() => {
  const bucket = result.value?.buckets[0];
  if (!bucket?.fit || !bucket.n) return '';
  const r = bucket.fit.r ?? 0;
  const r2 = bucket.fit.r2 ?? 0;
  const parts = [
    t('plots.spaces_count', bucket.n),
    `r = ${r.toFixed(2)}`,
    `R² = ${r2.toFixed(2)}`,
  ];
  if (bucket.sampled) parts.push(t('plots.sampled'));
  return parts.join(' · ');
});

/**
 * Pairs for every metric, then the metric: keeps it while it has pairs, else
 * the default, else the first.
 */
async function probeAll(): Promise<void> {
  const slug = parameter.value;
  await Promise.all(
    [...probes].map(([key, probe]) => {
      const params: ExploreParams | null = slug
        ? {
            // the pollutant fitted on the metric
            agg: 'pairs',
            x: key,
            y: slug,
            filter: exploreFilter(),
            ...exploreRange(),
          }
        : null;
      return probe.load(params);
    }),
  );
  const keys = metricOptions.value.map((opt) => opt.value);
  if (metric.value && keys.includes(metric.value)) return;
  metric.value = keys.includes(props.defaultMetric)
    ? props.defaultMetric
    : (keys[0] ?? null);
}

/** Settle the pollutant, then probe: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  await parameters.refresh();
  await probeAll();
}

function onParameter(value: string | null): void {
  parameter.value = value;
  void probeAll();
}

/** every metric is already loaded: switching only redraws */
function onMetric(value: string | null): void {
  metric.value = value;
}

onMounted(() => void refresh());
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refresh());
});

const option = computed<EChartsOption>(() => {
  const value = result.value;
  const bucket = value?.buckets[0];
  const points = bucket?.points || [];
  if (!bucket || !points.length) {
    return {};
  }
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
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
  const xName = metricLabel.value;
  const yName = `${parameterLabel.value}${unit.value ? ` (${unit.value})` : ''}`;
  const spaceName = t('plots.spaces');
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
        { name: spaceName, icon: 'circle' },
        ...(line.length ? [{ name: fitName }] : []),
      ],
    },
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const item = Array.isArray(p) ? p[0] : p;
        if (!item || item.seriesName !== spaceName) return '';
        const [x, y] = item.value as [number, number];
        return `${xName}: <b>${formatValue(x)}</b><br/>${yName}: <b>${formatValue(y)}</b>`;
      },
    },
    grid: { left: 16, right: 24, top: 36, bottom: 56, containLabel: true },
    xAxis: {
      type: 'value',
      scale: true,
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
      // concentrations stay on the positive side; the fit line is clipped
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
        name: spaceName,
        data: points,
        symbolSize: 7,
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
</script>
