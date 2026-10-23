<template>
  <ChartCard :eyebrow="eyebrowText" :title="title">
    <template #controls>
      <span>{{ t('explore_figures.relationship.plot_mean') }}</span>
      <q-btn-dropdown
        v-if="parameterOptions.length > 1"
        class="relationship-figure__chip"
        :label="chipLabel"
        no-caps
        unelevated
        rounded
        dense
        color="grey-10"
      >
        <q-list dense>
          <q-item
            v-for="opt in parameterOptions"
            :key="opt.value"
            v-close-popup
            clickable
            :active="opt.value === parameter"
            @click="onParameter(opt.value)"
          >
            <q-item-section>{{ opt.label }}</q-item-section>
          </q-item>
        </q-list>
      </q-btn-dropdown>
      <span v-else class="relationship-figure__chip relationship-figure__chip--static">{{ chipLabel }}</span>
      <span>{{ t('explore_figures.relationship.against') }}</span>
      <q-select
        :model-value="metric"
        :options="metricOptions"
        :loading="probing"
        emit-value
        map-options
        dense
        outlined
        options-dense
        class="relationship-figure__metric"
        @update:model-value="(value) => (metric = value)"
      />
    </template>
    <FigureFrame :height="height" :loading="loading" :error="error" :empty="emptyMessage">
      <e-charts autoresize :init-options="initOptions" :option="option" :update-options="updateOptions" />
    </FigureFrame>
    <template #footer>
      <span class="relationship-figure__summary">{{ summary }}</span>
    </template>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * A pollutant against a space characteristic, a point per space (its mean
 * over the period), with the least-squares line and the pollutant's
 * reference. Every metric is probed at once: switching only redraws.
 */
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { LineChart, ScatterChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, MarkLineComponent, TooltipComponent } from 'echarts/components';
import ChartCard from '@/components/explore/ChartCard.vue';
import FigureFrame from '@/components/explore/FigureFrame.vue';
import {
  FIGURE_ACCENT,
  FIGURE_GAP,
  GRID,
  MUTED,
  benchmarkOf,
  initOptions,
  shortParameterName,
  updateOptions,
} from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useParameterChoice } from '@/composables/useContextScope';
import { useExploreRequest } from '@/composables/useExploreQuery';

use([SVGRenderer, ScatterChart, LineChart, GridComponent, MarkLineComponent, TooltipComponent]);

interface Props {
  title: string;
  /** height of the plot area */
  height?: number;
  /** catalog metric the figure opens on, when it has pairs */
  defaultMetric?: string;
}

const props = withDefaults(defineProps<Props>(), { height: 380, defaultMetric: 'space.occupancy_density' });
const i18n = useI18n();
const { t, locale } = i18n;
const { formatValue, describeReference } = useChartFormat();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const parameters = useParameterChoice();
const { parameter, parameterOptions, parameterLabel } = parameters;
const metric = ref<string | null>(null);

/** one pairs request per catalog metric: the menu lists those with pairs */
const probes = new Map((exploreStore.schema?.metrics || []).map((key) => [key, useExploreRequest('relationships')] as const));
const current = computed(() => (metric.value ? probes.get(metric.value) : undefined));
const result = computed(() => current.value?.result.value ?? null);
const probing = computed(() => [...probes.values()].some((probe) => probe.loading.value));
const loading = computed(() => probing.value);
const error = computed(
  () => current.value?.error.value ?? [...probes.values()].find((probe) => probe.error.value)?.error.value ?? null,
);

function metricName(key: string): string {
  const path = `plots.metrics.${key.replace('.', '_')}`;
  return i18n.te(path) ? t(path) : key;
}

const metricOptions = computed(() =>
  [...probes.entries()].flatMap(([key, probe]) => (probe.result.value?.meta.n ? [{ value: key, label: metricName(key) }] : [])),
);

const chipLabel = computed(() => (parameter.value ? shortParameterName(parameter.value) : '–'));

const eyebrowText = computed(() =>
  t('explore_figures.relationship.eyebrow', {
    pollutant: parameter.value ? parameterLabel.value : t('explore_figures.groups.pollutant'),
  }),
);

const emptyMessage = computed(() => {
  if (probing.value || metric.value) return '';
  const metrics = new Intl.ListFormat(locale.value, { type: 'disjunction' }).format(
    [...probes.keys()].map((key) => metricName(key).toLowerCase()),
  );
  return t('plots.no_pairs', { parameter: parameterLabel.value, metrics });
});

const benchmark = computed(() => benchmarkOf(exploreStore.schema, parameter.value));

/** spaces, correlation and fit quality, under the figure */
const summary = computed(() => {
  const bucket = result.value?.buckets[0];
  if (!bucket?.fit || !bucket.n) return '';
  const parts = [
    t('plots.spaces_count', bucket.n),
    `r = ${(bucket.fit.r ?? 0).toFixed(2)}`,
    `R² = ${(bucket.fit.r2 ?? 0).toFixed(2)}`,
  ];
  if (bucket.sampled) parts.push(t('plots.sampled'));
  return parts.join(' · ');
});

/** Pairs for every metric, then the metric: kept while it has pairs, else the default, else the first. */
async function probeAll(): Promise<void> {
  const slug = parameter.value;
  await Promise.all(
    [...probes].map(([key, probe]) =>
      probe.load(slug ? { agg: 'pairs', x: key, y: slug, filter: exploreFilter(), ...exploreRange() } : null),
    ),
  );
  const keys = metricOptions.value.map((opt) => opt.value);
  if (metric.value && keys.includes(metric.value)) return;
  metric.value = keys.includes(props.defaultMetric) ? props.defaultMetric : (keys[0] ?? null);
}

/** Settle the pollutant, then probe: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  await parameters.refresh();
  await probeAll();
}

function onParameter(value: string): void {
  parameter.value = value;
  void probeAll();
}

onMounted(() => void refresh());
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refresh());
});

const option = computed<EChartsOption>(() => {
  const bucket = result.value?.buckets[0];
  const points = bucket?.points || [];
  if (!bucket || !points.length) return {};
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
  const b = benchmark.value;
  const unit = result.value?.meta.unit ? ` ${result.value.meta.unit}` : '';
  const xName = metricName(metric.value ?? '');
  const axisLabel = { color: MUTED, fontSize: 11 };
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const item = Array.isArray(p) ? p[0] : p;
        if (!item || item.seriesType !== 'scatter') return '';
        const [x, y] = item.value as [number, number];
        return `${xName}: <b>${formatValue(x)}</b><br/>${parameterLabel.value}: <b>${formatValue(y)}${unit}</b>`;
      },
    },
    grid: { left: 0, right: 8, top: 16, bottom: 0, containLabel: true },
    xAxis: {
      type: 'value',
      scale: true,
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel,
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      scale: true,
      // concentrations stay on the positive side; the reference stays in view
      ...(Math.min(...ys) >= 0 ? { min: 0 } : {}),
      ...(b ? { max: (extent: { max: number }) => Math.max(extent.max, b.value * 1.1) } : {}),
      splitNumber: 4,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { ...axisLabel, formatter: (v: number) => formatValue(v) },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: [
      {
        type: 'scatter',
        data: points,
        symbolSize: 7,
        itemStyle: { color: FIGURE_ACCENT, opacity: 0.8 },
        cursor: 'default',
        clip: false,
        ...(b
          ? {
              markLine: {
                silent: true,
                symbol: 'none',
                lineStyle: { color: FIGURE_GAP, type: 'solid' as const, width: 1.5 },
                label: {
                  position: 'insideEndTop' as const,
                  distance: 6,
                  padding: [2, 0, 4, 0],
                  lineHeight: 16,
                  color: FIGURE_GAP,
                  fontSize: 11,
                  formatter: t('explore_figures.pattern.reference', { value: describeReference(b) }),
                },
                data: [{ yAxis: b.value }],
              },
            }
          : {}),
      },
      ...(line.length
        ? [
            {
              type: 'line' as const,
              data: line,
              symbol: 'none',
              silent: true,
              lineStyle: { color: '#212121', width: 1.5 },
            },
          ]
        : []),
    ],
  };
});
</script>

<style scoped lang="scss">
.relationship-figure__chip {
  padding: 2px 14px;
  font-size: 0.9375rem;
}

.relationship-figure__chip--static {
  border-radius: 999px;
  background: $grey-10;
  color: white;
}

.relationship-figure__metric {
  min-width: 180px;

  :deep(.q-field__control) {
    border-radius: 2px;
  }
}

.relationship-figure__summary {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: $grey-8;
}
</style>
