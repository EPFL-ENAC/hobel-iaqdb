<template>
  <div ref="root">
    <ChartCard :eyebrow="eyebrow" :title="title">
      <template #actions>
        <span class="pair-figure__label">{{ t('explore_figures.correlation.method') }}</span>
        <FigureToggle :model-value="method" :options="methodOptions" @update:model-value="onMethod" />
        <span class="pair-figure__label">X</span>
        <q-select
          :model-value="x"
          :options="xOptions"
          :loading="coverage.loading.value || probeY.loading.value"
          :display-value="x ? shortParameterName(x) : ''"
          emit-value
          map-options
          dense
          outlined
          options-dense
          class="pair-figure__select"
          @update:model-value="onX"
        />
        <span class="pair-figure__label">Y</span>
        <q-select
          :model-value="y"
          :options="yOptions"
          :loading="probe.loading.value"
          :display-value="y ? shortParameterName(y) : ''"
          emit-value
          map-options
          dense
          outlined
          options-dense
          class="pair-figure__select"
          @update:model-value="onY"
        />
      </template>
      <div class="pair-figure__body">
        <aside class="pair-figure__facts">
          <div class="pair-figure__r">
            <span class="pair-figure__r-symbol">r</span>
            <span class="pair-figure__r-value">{{ r === null ? '–' : r.toFixed(2) }}</span>
          </div>
          <div class="pair-figure__method">{{ methodLabel }}</div>
          <dl class="pair-figure__list">
            <template v-for="fact in facts" :key="fact.label">
              <dt>{{ fact.label }}</dt>
              <dd>{{ fact.value }}</dd>
            </template>
          </dl>
          <p class="pair-figure__note">{{ t('explore_figures.pair.note') }}</p>
        </aside>
        <FigureFrame :height="height" :loading="loading" :error="error" :empty="emptyMessage" class="pair-figure__plot">
          <e-charts autoresize :init-options="initOptions" :option="option" :update-options="updateOptions" />
        </FigureFrame>
      </div>
    </ChartCard>
  </div>
</template>

<script setup lang="ts">
/**
 * Any two variables measured in the same space at the same hour: a sample of
 * the hourly pairs as dots, the least-squares line over every pair, and the
 * correlation by the method picked. A correlation matrix cell opens its pair here.
 */
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { LineChart, ScatterChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, TooltipComponent } from 'echarts/components';
import ChartCard from '@/components/explore/ChartCard.vue';
import FigureFrame from '@/components/explore/FigureFrame.vue';
import FigureToggle from '@/components/explore/FigureToggle.vue';
import { FIGURE_ACCENT, GRID, MUTED, initOptions, shortParameterName, updateOptions } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useParametersWithRecords } from '@/composables/useContextScope';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type { ExploreParams } from '@/models';

use([SVGRenderer, ScatterChart, LineChart, GridComponent, TooltipComponent]);

interface Props {
  eyebrow: string;
  title: string;
  /** height of the plot area */
  height?: number;
}

type Method = 'pearson' | 'spearman';

withDefaults(defineProps<Props>(), { height: 320 });
const { t, locale } = useI18n();
const { formatValue } = useChartFormat();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

/** the pair the figure opens on, when both have data together */
const DEFAULT_X = 'pm2_5';
const DEFAULT_Y = 'pm10';

const root = ref<HTMLElement | null>(null);
const x = ref<string | null>(null);
const y = ref<string | null>(null);
const method = ref<Method>('spearman');
/** variables measured together with x */
const partners = ref<Set<string>>(new Set());
/** variables measured together with y; null while there is no y */
const partnersOfY = ref<Set<string> | null>(null);

const coverage = useParametersWithRecords();
/** the partners of x: the Y menu */
const probe = useExploreRequest('relationships');
/** the partners of y: the X menu */
const probeY = useExploreRequest('relationships');
/** the dots and the least-squares line, with Pearson's r */
const pairsRequest = useExploreRequest('relationships');
/** Spearman's r of the pair: a matrix of two */
const rankRequest = useExploreRequest('relationships');

const loading = computed(() => pairsRequest.loading.value || rankRequest.loading.value);
const error = computed(() => pairsRequest.error.value);
const emptyMessage = computed(() => (pairsRequest.empty.value ? t('plots.no_common_hours') : ''));

/** only the variables measured in the same space and hour as y */
const xOptions = computed(() =>
  coverage.options.value.filter((opt) => !partnersOfY.value || partnersOfY.value.has(opt.value)),
);
/** only the variables measured in the same space and hour as x */
const yOptions = computed(() => coverage.options.value.filter((opt) => partners.value.has(opt.value)));

const methodOptions = computed<{ value: Method; label: string }[]>(() => [
  { value: 'pearson', label: t('plots.pearson') },
  { value: 'spearman', label: t('plots.spearman') },
]);
const methodLabel = computed(() => t(`explore_figures.pair.${method.value}`));

const bucket = computed(() => pairsRequest.result.value?.buckets[0] ?? null);

/** Pearson's from the pairs, Spearman's from the matrix of two */
const r = computed<number | null>(() => {
  if (method.value === 'pearson') return bucket.value?.fit?.r ?? null;
  return rankRequest.result.value?.buckets[0]?.fit?.r ?? null;
});

function unitOf(slug: string | null): string {
  return exploreStore.schema?.parameters.find((p) => p.slug === slug)?.unit ?? '';
}

const facts = computed(() => {
  const b = bucket.value;
  if (!b?.n) return [];
  const fit = b.fit;
  const points = b.points?.length ?? 0;
  return [
    { label: t('explore_figures.pair.pairs'), value: t('explore_figures.pair.hours', { count: b.n.toLocaleString(locale.value) }) },
    ...(fit?.slope !== undefined && fit.intercept !== undefined
      ? [
          {
            label: t('explore_figures.pair.trend'),
            value: `y = ${formatValue(fit.slope)}x ${fit.intercept < 0 ? '−' : '+'} ${formatValue(Math.abs(fit.intercept))}`,
          },
        ]
      : []),
    {
      label: t('explore_figures.pair.shown'),
      value: b.sampled
        ? t('explore_figures.pair.sampled', { count: points.toLocaleString(locale.value) })
        : t('explore_figures.pair.all', { count: points.toLocaleString(locale.value) }),
    },
  ];
});

function scope(): Pick<ExploreParams, 'filter' | 'from' | 'to'> {
  return { filter: exploreFilter(), ...exploreRange() };
}

/** The variables measured with `slug`; null when a later load aborted this one. */
async function partnersOf(request: typeof probe, slug: string): Promise<Set<string> | null> {
  const value = await request.load({ agg: 'partners', x: slug, ...scope() });
  if (!value) return null;
  return new Set(value.buckets.flatMap((b) => (b.n && b.key[0] ? [b.key[0]] : [])));
}

/**
 * Variables with records, then x: kept while offered, else the default, else
 * the first; one measured with nothing is passed over, as its Y menu would be empty.
 */
async function settleX(): Promise<boolean> {
  await coverage.refresh();
  const offered = coverage.options.value.map((opt) => opt.value);
  const first = x.value && offered.includes(x.value) ? x.value : offered.includes(DEFAULT_X) ? DEFAULT_X : offered[0];
  const candidates = first ? [first, ...offered.filter((slug) => slug !== first)] : [];
  for (const slug of candidates) {
    const found = await partnersOf(probe, slug);
    if (!found) return false;
    if (!found.size) continue;
    x.value = slug;
    partners.value = found;
    return true;
  }
  x.value = null;
  partners.value = new Set();
  return true;
}

/** The partners of x, for the Y menu. */
async function loadPartners(): Promise<boolean> {
  if (!x.value) {
    partners.value = new Set();
    return true;
  }
  const found = await partnersOf(probe, x.value);
  if (!found) return false;
  partners.value = found;
  return true;
}

/** Y among the partners of x: the one asked for, else kept, else the default, else the first. */
function settleY(preferred: string | null = null): void {
  const offered = yOptions.value.map((opt) => opt.value);
  if (preferred && offered.includes(preferred)) y.value = preferred;
  else if (y.value && offered.includes(y.value)) return;
  else y.value = offered.includes(DEFAULT_Y) ? DEFAULT_Y : (offered[0] ?? null);
}

/** The partners of y, for the X menu; x is one of them, as y is a partner of x. */
async function narrowX(): Promise<void> {
  if (!y.value) {
    partnersOfY.value = null;
    return;
  }
  const found = await partnersOf(probeY, y.value);
  if (found) partnersOfY.value = found;
}

function reload(): void {
  const pair = x.value && y.value ? { x: x.value, y: y.value } : null;
  void pairsRequest.load(pair ? { agg: 'pairs', ...pair, ...scope() } : null);
  void rankRequest.load(
    pair && method.value === 'spearman'
      ? { agg: 'matrix', parameters: [pair.x, pair.y], method: 'spearman', ...scope() }
      : null,
  );
}

/** Settle both menus, then load: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  if (!(await settleX())) return;
  settleY();
  reload();
  await narrowX();
}

async function onX(value: string | null): Promise<void> {
  x.value = value;
  if (!(await loadPartners())) return;
  settleY();
  reload();
  await narrowX();
}

function onY(value: string | null): void {
  y.value = value;
  reload();
  void narrowX();
}

function onMethod(value: Method): void {
  method.value = value;
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
  void loadPartners().then((settled) => {
    if (!settled) return;
    settleY(py);
    reload();
    void narrowX();
  });
});

const option = computed<EChartsOption>(() => {
  const b = bucket.value;
  const points = b?.points || [];
  if (!b || !points.length) return {};
  const xs = points.map(([px]) => px);
  const ys = points.map(([, py]) => py);
  const lo = Math.min(...xs);
  const hi = Math.max(...xs);
  const fit = b.fit;
  const line =
    fit?.slope !== undefined && fit.intercept !== undefined
      ? [
          [lo, fit.slope * lo + fit.intercept],
          [hi, fit.slope * hi + fit.intercept],
        ]
      : [];
  const xName = [x.value ? shortParameterName(x.value) : '', unitOf(x.value)].filter(Boolean).join(' ');
  const yName = [y.value ? shortParameterName(y.value) : '', unitOf(y.value)].filter(Boolean).join(' ');
  const axisLabel = { color: MUTED, fontSize: 11, formatter: (v: number) => formatValue(v) };
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const item = Array.isArray(p) ? p[0] : p;
        if (!item || item.seriesType !== 'scatter') return '';
        const [px, py] = item.value as [number, number];
        return `${xName}: <b>${formatValue(px)}</b><br/>${yName}: <b>${formatValue(py)}</b>`;
      },
    },
    grid: { left: 0, right: 16, top: 28, bottom: 24, containLabel: true },
    xAxis: {
      type: 'value',
      scale: true,
      // concentrations stay on the positive side; the trend line is clipped
      ...(lo >= 0 ? { min: 0 } : {}),
      name: `${xName} →`,
      nameLocation: 'end',
      nameGap: 8,
      nameTextStyle: { color: MUTED, fontSize: 11, align: 'right', verticalAlign: 'top', padding: [14, 0, 0, 0] },
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel,
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      scale: true,
      ...(Math.min(...ys) >= 0 ? { min: 0 } : {}),
      splitNumber: 3,
      name: `↑ ${yName}`,
      nameLocation: 'end',
      nameGap: 12,
      nameTextStyle: { color: MUTED, fontSize: 11, align: 'left' },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel,
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: [
      {
        type: 'scatter',
        data: points,
        symbolSize: 6,
        itemStyle: { color: FIGURE_ACCENT, opacity: 0.75 },
        cursor: 'default',
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
.pair-figure__label {
  font-size: 0.875rem;
  color: $grey-7;
}

.pair-figure__select {
  min-width: 96px;

  :deep(.q-field__control) {
    border-radius: 2px;
  }
}

.pair-figure__body {
  display: grid;
  grid-template-columns: minmax(200px, 260px) minmax(0, 1fr);
  gap: 48px;
  flex: 1;

  @media (max-width: $breakpoint-sm-max) {
    grid-template-columns: minmax(0, 1fr);
    gap: 24px;
  }
}

.pair-figure__facts {
  color: $grey-10;
}

.pair-figure__r {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.pair-figure__r-symbol {
  font-size: 0.9375rem;
  font-style: italic;
  color: $grey-8;
}

.pair-figure__r-value {
  font-size: 2.25rem;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.pair-figure__method {
  margin: 4px 0 24px;
  font-size: 0.9375rem;
  color: $grey-8;
}

.pair-figure__list {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 6px 24px;
  margin: 0 0 24px;
  font-size: 0.9375rem;

  dt {
    color: $grey-8;
  }

  dd {
    margin: 0;
  }
}

.pair-figure__note {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: $grey-8;
}

.pair-figure__plot {
  min-width: 0;
}
</style>
