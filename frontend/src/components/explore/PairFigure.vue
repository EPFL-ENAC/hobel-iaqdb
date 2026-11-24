<template>
  <div ref="root">
    <ChartCard :eyebrow="eyebrow" :title="title">
      <template #actions>
        <span class="figure-field">
          <span class="pair-figure__label">{{ t('explore_figures.correlation.method') }}</span>
          <FigureToggle :model-value="method" :options="methodOptions" @update:model-value="onMethod" />
        </span>
        <span class="figure-field">
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
        </span>
        <span class="figure-field">
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
        </span>
        <FigureMenu
          :label="t('explore_figures.split.label')"
          :model-value="split"
          :options="splitOptions"
          @update:model-value="onSplit"
        />
      </template>
      <!-- split: one small chart per group, under the menus -->
      <template v-if="splitShown">
        <!-- at least one small chart tall: a row of them is always taller, so no blank band under it -->
        <FigureFrame :height="PANEL_HEIGHT" fit="content" :loading="loading" :error="error" :empty="emptyMessage">
          <SplitPanels
            :dimension="splitShown"
            :buckets="pairsRequest.result.value?.buckets ?? []"
            :method="method"
            :title="pairTitle"
            :option-of="panelOption"
            :facts-of="panelFacts"
            :points-label="t('explore_figures.studies.paired_hours')"
            :height="PANEL_HEIGHT"
          />
        </FigureFrame>
        <p class="pair-figure__note pair-figure__note--split">{{ t('explore_figures.pair.note') }}</p>
      </template>
      <div v-else class="pair-figure__body">
        <aside class="pair-figure__facts">
          <div class="pair-figure__r">
            <span class="pair-figure__r-symbol">r</span>
            <span class="pair-figure__r-value">{{ r === null ? '–' : r.toFixed(2) }}</span>
          </div>
          <div class="pair-figure__method">{{ methodLabel }}</div>
          <StudySpread :within="within" />
          <dl class="pair-figure__list">
            <template v-for="fact in facts" :key="fact.label">
              <dt>{{ fact.label }}</dt>
              <!-- the number of studies opens their list -->
              <dd v-if="fact.studies">
                <StudiesDialog
                  :title="pairTitle"
                  v-bind="{ method, r, within, pointsLabel: t('explore_figures.studies.paired_hours') }"
                  >{{ fact.value }}</StudiesDialog
                >
              </dd>
              <dd v-else>{{ fact.value }}</dd>
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
 * correlation by the method picked. "Split by" draws one small chart per
 * group (#229). A correlation matrix cell opens its pair here.
 */
import ECharts from 'vue-echarts';
import { use } from 'echarts/core';
import { LineChart, ScatterChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, TooltipComponent } from 'echarts/components';
import ChartCard from '@/components/explore/ChartCard.vue';
import FigureFrame from '@/components/explore/FigureFrame.vue';
import FigureMenu from '@/components/explore/FigureMenu.vue';
import FigureToggle from '@/components/explore/FigureToggle.vue';
import SplitPanels from '@/components/explore/SplitPanels.vue';
import StudiesDialog from '@/components/explore/StudiesDialog.vue';
import StudySpread from '@/components/explore/StudySpread.vue';
import { initOptions, shortParameterName, updateOptions } from '@/components/plots/charts';
import { type ScatterSpec, scatterOption, splitRanges } from '@/components/plots/scatter';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useParametersWithRecords, useSplitChoice } from '@/composables/useContextScope';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type { ExploreBucket, ExploreParams } from '@/models';

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

/** the pair the figure opens on, when both have data together: the one most survey respondents asked for (#229) */
const DEFAULT_X = 'co2';
const DEFAULT_Y = 'pm2_5';

const root = ref<HTMLElement | null>(null);
const x = ref<string | null>(null);
const y = ref<string | null>(null);
const method = ref<Method>('spearman');
const { split, splitOptions } = useSplitChoice();
/** variables measured together with x, enough for a correlation */
const partners = ref<Set<string>>(new Set());
/** variables measured together with y, enough for a correlation; null while there is no y */
const partnersOfY = ref<Set<string> | null>(null);

const coverage = useParametersWithRecords();
/** the partners of x: the Y menu */
const probe = useExploreRequest('relationships');
/** the partners of y: the X menu */
const probeY = useExploreRequest('relationships');
/** the dots, the least-squares line and r by the method, per group of the split */
const pairsRequest = useExploreRequest('relationships');

const loading = computed(() => pairsRequest.loading.value);
const error = computed(() => pairsRequest.error.value);
const emptyMessage = computed(() => {
  if (pairsRequest.empty.value) return t('plots.no_common_hours');
  // x has partners, but none with enough data: the Y menu is empty
  if (x.value && !y.value && !probe.loading.value) return t('plots.too_little_data');
  return '';
});

/** only the variables measured in the same space and hour as y, with enough data */
const xOptions = computed(() =>
  coverage.options.value.filter((opt) => !partnersOfY.value || partnersOfY.value.has(opt.value)),
);
/** only the variables measured in the same space and hour as x, with enough data */
const yOptions = computed(() => coverage.options.value.filter((opt) => partners.value.has(opt.value)));

const methodOptions = computed<{ value: Method; label: string }[]>(() => [
  { value: 'pearson', label: t('plots.pearson') },
  { value: 'spearman', label: t('plots.spearman') },
]);
/** the split of the result on show, which the menu runs ahead of while it loads */
const splitShown = computed(() => pairsRequest.result.value?.meta.dimensions[0] ?? null);
/** all the pairs, without a split */
const bucket = computed(() => (splitShown.value ? null : (pairsRequest.result.value?.buckets[0] ?? null)));
const pairTitle = computed(() => `${shortParameterName(x.value ?? '')} × ${shortParameterName(y.value ?? '')}`);

/** the method, or why there is no r */
const methodLabel = computed(() =>
  bucket.value?.enough === false ? t('plots.too_little_data') : t(`explore_figures.pair.${method.value}`),
);

/** by the method of the request */
const r = computed<number | null>(() => bucket.value?.fit?.r ?? null);
const within = computed(() => bucket.value?.within);

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
    ...(b.n_studies !== undefined
      ? [{ label: t('explore_figures.pair.studies'), value: b.n_studies.toLocaleString(locale.value), studies: true }]
      : []),
    ...(b.n_spaces !== undefined
      ? [{ label: t('explore_figures.pair.spaces'), value: b.n_spaces.toLocaleString(locale.value) }]
      : []),
    ...(fit?.slope != null && fit.intercept != null
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

/**
 * The variables measured with `slug`, leaving out the pairs below the minimum
 * sample size; null when a later load aborted this one.
 */
async function partnersOf(request: typeof probe, slug: string): Promise<Set<string> | null> {
  const value = await request.load({ agg: 'partners', x: slug, ...scope() });
  if (!value) return null;
  return new Set(value.buckets.flatMap((b) => (b.n && b.enough !== false && b.key[0] ? [b.key[0]] : [])));
}

/**
 * Variables with records, then x: kept while offered, else the default, else
 * the first; one with no partner above the minimum is passed over, as its Y menu would be empty.
 * The first pick is probed alone; past it one request names every variable
 * measured with another, not a probe each.
 */
async function settleX(): Promise<boolean> {
  await coverage.refresh();
  const offered = coverage.options.value.map((opt) => opt.value);
  const first = x.value && offered.includes(x.value) ? x.value : offered.includes(DEFAULT_X) ? DEFAULT_X : offered[0];
  if (first) {
    const found = await partnersOf(probe, first);
    if (!found) return false;
    if (found.size) {
      x.value = first;
      partners.value = found;
      return true;
    }
  }
  const partnered = await probe.load({ agg: 'partnered', ...scope() });
  if (!partnered) return false;
  const withAny = new Set(partnered.buckets.flatMap((b) => (b.n && b.key[0] ? [b.key[0]] : [])));
  x.value = offered.find((slug) => withAny.has(slug)) ?? null;
  return loadPartners();
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
  const by = split.value ? { by: [split.value] } : {};
  void pairsRequest.load(pair ? { agg: 'pairs', ...pair, method: method.value, ...by, ...scope() } : null);
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

function onSplit(value: string | null): void {
  split.value = value;
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

const PAIR_STYLE = { dot: 6, opacity: 0.75, yTicks: 3 };
const PANEL_STYLE = { dot: 4, opacity: 0.6, yTicks: 3 };
/** height of each small chart of a split */
const PANEL_HEIGHT = 180;

/** the scatter of the pair, alone or as a small chart of the split */
function specOf(b: ExploreBucket): ScatterSpec {
  const xName = [x.value ? shortParameterName(x.value) : '', unitOf(x.value)].filter(Boolean).join(' ');
  const yName = [y.value ? shortParameterName(y.value) : '', unitOf(y.value)].filter(Boolean).join(' ');
  return {
    points: b.points ?? [],
    fit: b.fit,
    style: PAIR_STYLE,
    xZero: true,
    formatX: formatValue,
    formatY: formatValue,
    tooltip: (px, py) => `${xName}: <b>${formatValue(px)}</b><br/>${yName}: <b>${formatValue(py)}</b>`,
    names: { x: xName, y: yName },
  };
}

const option = computed(() => (bucket.value ? scatterOption(specOf(bucket.value)) : {}));

/** every group on the same axes */
const ranges = computed(() =>
  splitRanges(pairsRequest.result.value?.buckets ?? [], { xZero: true, yTicks: PANEL_STYLE.yTicks }),
);

function panelOption(b: ExploreBucket) {
  return scatterOption({ ...specOf(b), style: PANEL_STYLE, ranges: ranges.value });
}

function panelFacts(b: ExploreBucket): string[] {
  return [
    t('plots.spaces_count', b.n_spaces ?? 0),
    t('explore_figures.pair.hours', { count: b.n.toLocaleString(locale.value) }),
  ];
}
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

.pair-figure__note--split {
  margin-top: 16px;
}

.pair-figure__plot {
  min-width: 0;
}
</style>
