<template>
  <ChartCard :eyebrow="eyebrowText" :title="title">
    <template #controls>
      <span class="figure-field">
        <span>{{ t('explore_figures.relationship.plot_mean') }}</span>
        <!-- a pollutant fixed by the filter bar, or the only one with pairs, is said, not offered -->
        <q-select
          v-if="parameterOptions.length > 1"
          :model-value="parameter"
          :options="parameterOptions"
          emit-value
          map-options
          dense
          outlined
          options-dense
          class="relationship-figure__select"
          @update:model-value="onParameter"
        />
        <span v-else class="relationship-figure__pollutant">{{ pollutantName }}</span>
      </span>
      <!-- no metric with enough pairs: nothing to pick, the chart says why -->
      <template v-if="metricOptions.length">
        <span class="figure-field">
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
            class="relationship-figure__select"
            @update:model-value="onMetric"
          />
        </span>
        <FigureMenu
          :label="t('explore_figures.split.label')"
          :model-value="split"
          :options="splitOptions"
          @update:model-value="onSplit"
        />
      </template>
    </template>
    <!-- at least one small chart tall: a row of them is always taller, so no blank band under it -->
    <FigureFrame v-if="splitBuckets" :height="PANEL_HEIGHT" fit="content" :loading="loading" :error="error">
      <SplitPanels
        :dimension="splitBuckets.dimension"
        :buckets="splitBuckets.buckets"
        method="pearson"
        :title="pairTitle"
        :option-of="panelOption"
        :facts-of="(b) => [t('plots.spaces_count', b.n)]"
        :height="PANEL_HEIGHT"
      />
    </FigureFrame>
    <FigureFrame v-else :height="height" :loading="loading" :error="error" :empty="emptyMessage">
      <e-charts autoresize :init-options="initOptions" :option="option" :update-options="updateOptions" />
    </FigureFrame>
    <template #footer>
      <!-- split: the reference line of the small charts, which have no room for its label -->
      <span v-if="splitBuckets" class="relationship-figure__summary">{{ referenceLabel }}</span>
      <span v-else class="relationship-figure__summary">
        <template v-if="summary && studies">
          <StudiesDialog :title="pairTitle" method="pearson" :r="bucket?.fit?.r" :within="bucket?.within">{{
            studies
          }}</StudiesDialog>
          ·
        </template>
        {{ summary }}
      </span>
    </template>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * A pollutant against a space characteristic, a point per space (its mean
 * over the period), with the least-squares line and the pollutant's
 * reference. Every metric is probed at once: switching only redraws. The
 * pollutant menu lists those with enough pairs for at least one metric.
 * "Split by" draws one small chart per group (#229), from one more request.
 */
import ECharts from 'vue-echarts';
import { use } from 'echarts/core';
import { LineChart, ScatterChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, MarkLineComponent, TooltipComponent } from 'echarts/components';
import ChartCard from '@/components/explore/ChartCard.vue';
import FigureFrame from '@/components/explore/FigureFrame.vue';
import FigureMenu from '@/components/explore/FigureMenu.vue';
import SplitPanels from '@/components/explore/SplitPanels.vue';
import StudiesDialog from '@/components/explore/StudiesDialog.vue';
import { benchmarkOf, initOptions, updateOptions } from '@/components/plots/charts';
import { type ScatterSpec, scatterOption, splitRanges } from '@/components/plots/scatter';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useParameterChoice, useSplitChoice } from '@/composables/useContextScope';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type { ExploreBucket } from '@/models';

use([SVGRenderer, ScatterChart, LineChart, GridComponent, MarkLineComponent, TooltipComponent]);

interface Props {
  title: string;
  /** height of the plot area */
  height?: number;
  /** catalog metric the figure opens on, when it has pairs */
  defaultMetric?: string;
}

const props = withDefaults(defineProps<Props>(), { height: 380, defaultMetric: 'space.occupancy_density' });
/** height of each small chart of a split */
const PANEL_HEIGHT = 160;
const i18n = useI18n();
const { t, locale } = i18n;
const { formatValue, formatYear, describeReference, describeWithin } = useChartFormat();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const metricKeys = exploreStore.schema?.metrics || [];
/** catalog metrics that are years: 1995, not 1,995 */
const YEAR_METRICS = new Set(['building.construction_year']);

/** one partners request per catalog metric: the pollutants measured where it is known */
const partners = new Map(metricKeys.map((key) => [key, useExploreRequest('relationships')] as const));

/** the pollutants with enough pairs for a correlation with at least one metric; null until known */
const paired = computed(() => {
  const results = [...partners.values()].map((request) => request.result.value);
  if (!results.length || results.some((result) => !result)) return null;
  return new Set(
    results.flatMap((result) =>
      (result?.buckets || []).flatMap((b) => (b.key[0] && b.n && b.enough !== false ? [b.key[0]] : [])),
    ),
  );
});

const parameters = useParameterChoice({ among: paired });
const { parameter, parameterOptions, parameterLabel } = parameters;
const metric = ref<string | null>(null);
const { split, splitOptions } = useSplitChoice();
/** the metric against the pollutant per group of the split */
const splitRequest = useExploreRequest('relationships');

/** one pairs request per catalog metric: the menu lists those with pairs */
const probes = new Map(metricKeys.map((key) => [key, useExploreRequest('relationships')] as const));
const current = computed(() => (metric.value ? probes.get(metric.value) : undefined));
const result = computed(() => current.value?.result.value ?? null);
const probing = computed(() => [...probes.values()].some((probe) => probe.loading.value));
const loading = computed(
  () => probing.value || splitRequest.loading.value || [...partners.values()].some((request) => request.loading.value),
);
const error = computed(
  () =>
    current.value?.error.value ??
    [...probes.values()].find((probe) => probe.error.value)?.error.value ??
    splitRequest.error.value,
);

/** the groups of the split on show, which the menu runs ahead of while they load */
const splitBuckets = computed(() => {
  const value = splitRequest.result.value;
  const dimension = value?.meta.dimensions[0];
  return dimension ? { dimension, buckets: value.buckets } : null;
});

function metricName(key: string): string {
  const path = `plots.metrics.${key.replace('.', '_')}`;
  return i18n.te(path) ? t(path) : key;
}

/** a metric below the minimum sample size for a correlation is left out */
const metricOptions = computed(() =>
  [...probes.entries()].flatMap(([key, probe]) => {
    const value = probe.result.value;
    if (!value?.meta.n || value.buckets[0]?.enough === false) return [];
    return [{ value: key, label: metricName(key) }];
  }),
);

function formatX(value: number): string {
  return metric.value && YEAR_METRICS.has(metric.value) ? formatYear(value) : formatValue(value);
}

/** r or R²; none below the minimum sample size */
function formatFit(value: number | null | undefined): string {
  return typeof value === 'number' ? value.toFixed(2) : '–';
}

const pollutantName = computed(() => (parameter.value ? parameterLabel.value : '–'));

const eyebrowText = computed(() =>
  t('explore_figures.relationship.eyebrow', {
    pollutant: parameter.value ? parameterLabel.value : t('explore_figures.groups.pollutant'),
  }),
);

const emptyMessage = computed(() => {
  if (probing.value || metric.value) return '';
  // pairs, but too few spaces for any metric: every metric is left out
  if ([...probes.values()].some((probe) => probe.result.value?.meta.n)) return t('plots.too_little_data');
  const metrics = new Intl.ListFormat(locale.value, { type: 'disjunction' }).format(
    [...probes.keys()].map((key) => metricName(key).toLowerCase()),
  );
  return t('plots.no_pairs', { parameter: parameterLabel.value, metrics });
});

const benchmark = computed(() => benchmarkOf(exploreStore.schema, parameter.value));

const bucket = computed(() => result.value?.buckets[0]);

/** the studies behind the dots, a link to their list, before the summary */
const studies = computed(() => {
  const n = bucket.value?.n_studies;
  return n === undefined ? '' : t('plots.studies_count', n);
});
const pairTitle = computed(() => `${metric.value ? metricName(metric.value) : ''} × ${pollutantName.value}`);

/** spaces, correlation and fit quality, then r within each study, under the figure */
const summary = computed(() => {
  const b = bucket.value;
  if (!b?.fit || !b.n) return '';
  const spaces = t('plots.spaces_count', b.n);
  if (b.enough === false) return `${spaces} · ${t('plots.too_little_data')}`;
  const parts = [spaces, `r = ${formatFit(b.fit.r)}`, `R² = ${formatFit(b.fit.r2)}`];
  if (b.sampled) parts.push(t('plots.sampled'));
  const within = describeWithin(b.within);
  if (within) parts.push(within);
  return parts.join(' · ');
});

/** Pairs for every metric, then the metric: kept while offered, else the default, else the first. */
async function probeAll(): Promise<void> {
  const slug = parameter.value;
  await Promise.all(
    [...probes].map(([key, probe]) =>
      probe.load(slug ? { agg: 'pairs', x: key, y: slug, filter: exploreFilter(), ...exploreRange() } : null),
    ),
  );
  const keys = metricOptions.value.map((opt) => opt.value);
  if (!metric.value || !keys.includes(metric.value)) {
    metric.value = keys.includes(props.defaultMetric) ? props.defaultMetric : (keys[0] ?? null);
  }
  await loadSplit();
}

/** The groups of the metric against the pollutant; none without a split. */
async function loadSplit(): Promise<void> {
  const slug = parameter.value;
  const x = metric.value;
  const by = split.value;
  await splitRequest.load(
    by && x && slug ? { agg: 'pairs', x, y: slug, by: [by], filter: exploreFilter(), ...exploreRange() } : null,
  );
}

function onMetric(value: string): void {
  metric.value = value;
  void loadSplit();
}

function onSplit(value: string | null): void {
  split.value = value;
  void loadSplit();
}

/** Which pollutants have pairs, then settle the pollutant, then probe: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  const params = { agg: 'partners' as const, filter: exploreFilter(), ...exploreRange() };
  await Promise.all([...partners].map(([key, request]) => request.load({ ...params, x: key })));
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

const STYLE = { dot: 7, opacity: 0.8, yTicks: 4 };
const PANEL_STYLE = { dot: 5, opacity: 0.7, yTicks: 3 };

const referenceLabel = computed(() =>
  benchmark.value ? t('explore_figures.pattern.reference', { value: describeReference(benchmark.value) }) : '',
);

/** the scatter of the metric, alone or as a small chart of the split */
function specOf(b: ExploreBucket): ScatterSpec {
  const unit = result.value?.meta.unit ? ` ${result.value.meta.unit}` : '';
  const xName = metricName(metric.value ?? '');
  const reference = benchmark.value?.value;
  return {
    points: b.points ?? [],
    fit: b.fit,
    style: STYLE,
    xZero: false,
    formatX,
    formatY: formatValue,
    tooltip: (x, y) => `${xName}: <b>${formatX(x)}</b><br/>${parameterLabel.value}: <b>${formatValue(y)}${unit}</b>`,
    reference: reference === undefined ? undefined : { value: reference, label: referenceLabel.value },
  };
}

const option = computed(() => (bucket.value ? scatterOption(specOf(bucket.value)) : {}));

/** every group on the same axes, the reference in view */
const ranges = computed(() =>
  splitRanges(splitBuckets.value?.buckets ?? [], {
    xZero: false,
    yTicks: PANEL_STYLE.yTicks,
    reference: benchmark.value?.value,
  }),
);

/** a small chart: the reference line without its label, which the footer gives */
function panelOption(b: ExploreBucket) {
  const spec = specOf(b);
  const reference = spec.reference && { value: spec.reference.value };
  return scatterOption({ ...spec, style: PANEL_STYLE, reference, ranges: ranges.value });
}
</script>

<style scoped lang="scss">
// as tall as a dense select: the controls keep their height without one
.relationship-figure__pollutant {
  line-height: 40px;
  color: $grey-10;
}

.relationship-figure__select {
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
