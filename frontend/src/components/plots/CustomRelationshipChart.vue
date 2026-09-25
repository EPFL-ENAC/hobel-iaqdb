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
import { useExploreRequest } from '@/composables/useExploreQuery';
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

/** the pair the chart opens on, when both have data together */
const DEFAULT_X = 'air_temperature';
const DEFAULT_Y = 'co2';
/** a matrix takes at most 10 parameters: x and 9 candidates per probe */
const PROBE_SIZE = 9;
const POINT_COLOR = 'rgba(47, 85, 150, 0.45)';
const FIT_COLOR = '#d32f2f';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';

const root = ref<HTMLElement | null>(null);
const x = ref<string | null>(null);
const y = ref<string | null>(null);
/** pollutants measured together with x, from the probes */
const partners = ref<Set<string>>(new Set());
const probing = ref(false);

const coverage = useExploreRequest('measurements');
const probes = useExploreRequest('relationships');
const { result, loading, error, load } = useExploreRequest('relationships');

/** every pollutant with records under the filters */
const xOptions = computed(() => {
  const withData = new Set(
    (coverage.result.value?.buckets || []).flatMap((b) =>
      b.key[0] && b.n_records ? [b.key[0]] : [],
    ),
  );
  return exploreStore.parameterOptions.filter((opt) => withData.has(opt.value));
});

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

function formatValue(value: number): string {
  return new Intl.NumberFormat(locale.value, {
    maximumFractionDigits: Math.abs(value) < 10 ? 2 : 0,
  }).format(value);
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
  await coverage.load({ agg: 'coverage', by: ['parameter'], ...scope() });
  const offered = xOptions.value.map((opt) => opt.value);
  if (x.value && offered.includes(x.value)) return;
  x.value = offered.includes(DEFAULT_X) ? DEFAULT_X : (offered[0] ?? null);
}

/**
 * Which pollutants were measured with x: matrices of x and up to 9
 * candidates each, keeping the pairs with paired hours. Then y: kept while
 * offered, else the default, else the first.
 */
async function settleY(): Promise<void> {
  const slug = x.value;
  const candidates = xOptions.value
    .map((opt) => opt.value)
    .filter((c) => c !== slug);
  const found = new Set<string>();
  if (slug) {
    probing.value = true;
    try {
      for (let i = 0; i < candidates.length; i += PROBE_SIZE) {
        const value = await probes.load({
          agg: 'matrix',
          parameters: [slug, ...candidates.slice(i, i + PROBE_SIZE)],
          ...scope(),
        });
        for (const bucket of value?.buckets || []) {
          const [a, b] = bucket.key;
          if (!bucket.n || !a || !b) continue;
          if (a === slug) found.add(b);
          else if (b === slug) found.add(a);
        }
      }
    } finally {
      probing.value = false;
    }
  }
  partners.value = found;
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
