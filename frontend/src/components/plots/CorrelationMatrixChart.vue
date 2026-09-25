<template>
  <div>
    <div class="row items-center q-col-gutter-sm q-mb-sm">
      <div class="col">
        <q-select
          :model-value="selected"
          :options="parameterOptions"
          :label="t('plots.pollutants_max', { max: MAX_PARAMETERS })"
          :loading="coverage.loading.value"
          multiple
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onParameters"
        >
          <!-- short chips (CO₂, PM2.5…); the menu keeps the full names -->
          <template #selected-item="scope">
            <q-chip
              dense
              removable
              size="sm"
              color="grey-3"
              text-color="grey-9"
              class="q-my-none q-ml-none q-mr-xs"
              :tabindex="scope.tabindex"
              @remove="scope.removeAtIndex(scope.index)"
            >
              {{ shortName(scope.opt.value) }}
            </q-chip>
          </template>
        </q-select>
      </div>
      <div class="col-auto" style="min-width: 150px">
        <q-select
          :model-value="method"
          :options="methodOptions"
          :label="t('plots.method')"
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onMethod"
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
    <div v-else-if="selected.length < 2" class="text-grey-7 text-caption">
      {{ t('plots.pick_two_pollutants') }}
    </div>
    <div v-else-if="empty" class="text-grey-7 text-caption">
      {{ t('plots.no_pairs_matrix') }}
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
import { HeatmapChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import {
  GridComponent,
  TooltipComponent,
  VisualMapComponent,
} from 'echarts/components';
import { initOptions, updateOptions } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type { ExploreParams } from '@/models';

use([
  SVGRenderer,
  HeatmapChart,
  GridComponent,
  TooltipComponent,
  VisualMapComponent,
]);

interface Props {
  /** height of the plot area */
  height?: number;
}

type Method = 'pearson' | 'spearman';

withDefaults(defineProps<Props>(), { height: 400 });
const { t, locale } = useI18n();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

/** the endpoint caps a matrix at 10 parameters (45 cells) */
const MAX_PARAMETERS = 10;
/** the pollutants the matrix opens on, when they have data */
const DEFAULT_SET = ['co2', 'pm2_5', 'tvoc', 'no2', 'co'];
/** short names for the axes; other pollutants use their label */
const SHORT: Record<string, string> = {
  co2: 'CO₂',
  co: 'CO',
  no: 'NO',
  no2: 'NO₂',
  nox: 'NOₓ',
  o3: 'O₃',
  so2: 'SO₂',
  pm1: 'PM1',
  pm2_5: 'PM2.5',
  pm4: 'PM4',
  pm10: 'PM10',
  tvoc: 'TVOC',
};
const NEGATIVE = '#b2182b';
const NEUTRAL = '#f7f7f7';
const POSITIVE = '#2166ac';
const TEXT = '#424242';
const MUTED = '#757575';

const selected = ref<string[]>([]);
const method = ref<Method>('pearson');

const coverage = useExploreRequest('measurements');
const { result, loading, error, empty, load } =
  useExploreRequest('relationships');

const methodOptions = computed(() => [
  { value: 'pearson', label: t('plots.pearson') },
  { value: 'spearman', label: t('plots.spearman') },
]);

/** every pollutant with records under the filters */
const parameterOptions = computed(() => {
  const withData = new Set(
    (coverage.result.value?.buckets || []).flatMap((b) =>
      b.key[0] && b.n_records ? [b.key[0]] : [],
    ),
  );
  return exploreStore.parameterOptions.filter((opt) => withData.has(opt.value));
});

function shortName(slug: string): string {
  return SHORT[slug] ?? exploreStore.parameterLabel(slug);
}

const grainLabel = computed(() =>
  result.value?.meta.grain === 'hour' ? t('plots.paired_hours') : '',
);

/** r of each pair, both orders */
const cells = computed(() => {
  const map = new Map<string, { r: number | null; n: number }>();
  for (const bucket of result.value?.buckets || []) {
    const [a, b] = bucket.key;
    if (!a || !b) continue;
    const cell = { r: bucket.n ? (bucket.fit?.r ?? null) : null, n: bucket.n };
    map.set(`${a}|${b}`, cell);
    map.set(`${b}|${a}`, cell);
  }
  return map;
});

/** the axis order: as the matrix returned it */
const order = computed(() => result.value?.meta.parameters || []);

/** the strongest pair, by |r|, and how many pollutants */
const summary = computed(() => {
  const slugs = order.value;
  if (!slugs.length) return '';
  let best: { pair: string; r: number } | null = null;
  for (const bucket of result.value?.buckets || []) {
    const [a, b] = bucket.key;
    const r = bucket.fit?.r;
    if (!a || !b || r === undefined || !bucket.n) continue;
    if (!best || Math.abs(r) > Math.abs(best.r))
      best = { pair: `${shortName(a)}–${shortName(b)}`, r };
  }
  const count = t('plots.levels.parameter', slugs.length);
  return best ? `${best.pair}: ${best.r.toFixed(2)} · ${count}` : count;
});

const option = computed<EChartsOption>(() => {
  const slugs = order.value;
  if (!slugs.length) return {};
  const names = slugs.map(shortName);
  const data = slugs.flatMap((y, j) =>
    slugs.map((x, i) => {
      const cell = x === y ? { r: 1, n: 0 } : cells.value.get(`${x}|${y}`);
      // a pair never measured together stays an empty, grey cell
      const r = cell?.r ?? null;
      return {
        value: [i, j, r ?? '-'],
        n: cell?.n ?? 0,
        // white text on the strongly coloured cells
        label: { color: r !== null && Math.abs(r) > 0.6 ? '#fff' : TEXT },
      };
    }),
  );
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const item = Array.isArray(p) ? p[0] : p;
        const point = item?.data as
          { value: [number, number, number | '-']; n: number } | undefined;
        if (!point) return '';
        const [i, j, r] = point.value;
        const x = slugs[i] ?? '';
        const y = slugs[j] ?? '';
        if (x === y) return `<b>${shortName(x)}</b>`;
        return [
          `<b>${shortName(x)} × ${shortName(y)}</b>`,
          r === '-' ? t('plots.no_common_hours') : `r = <b>${r.toFixed(2)}</b>`,
          t('plots.paired_hours_count', {
            count: point.n.toLocaleString(locale.value),
          }),
        ].join('<br/>');
      },
    },
    grid: { left: 8, right: 8, top: 8, bottom: 64, containLabel: true },
    xAxis: {
      type: 'category',
      data: names,
      position: 'top',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: TEXT, interval: 0 },
      splitArea: { show: false },
    },
    yAxis: {
      type: 'category',
      data: names,
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: TEXT, interval: 0 },
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      itemWidth: 12,
      itemHeight: 160,
      text: ['+1', '−1'],
      textStyle: { color: MUTED },
      inRange: { color: [NEGATIVE, NEUTRAL, POSITIVE] },
    },
    series: [
      {
        type: 'heatmap',
        data,
        cursor: 'default',
        itemStyle: { borderColor: '#fff', borderWidth: 2 },
        label: {
          show: true,
          formatter: (p) => {
            const r = (p.value as [number, number, number | '-'])[2];
            return r === '-' ? '–' : r.toFixed(2);
          },
          color: TEXT,
        },
        emphasis: { itemStyle: { borderColor: TEXT, borderWidth: 1 } },
      },
    ],
  };
});

function params(): ExploreParams | null {
  if (selected.value.length < 2) return null;
  return {
    agg: 'matrix',
    parameters: [...selected.value],
    method: method.value,
    filter: exploreFilter(),
    ...exploreRange(),
  };
}

/**
 * Pollutants with data, then the selection: keeps the pollutants that still
 * have data; with fewer than two, the global selection or the default set.
 */
async function settle(): Promise<void> {
  await coverage.load({
    agg: 'coverage',
    by: ['parameter'],
    filter: exploreFilter(),
    ...exploreRange(),
  });
  const offered = new Set(parameterOptions.value.map((opt) => opt.value));
  const kept = selected.value.filter((slug) => offered.has(slug));
  if (kept.length >= 2) {
    selected.value = kept;
    return;
  }
  const global = exploreStore.parameters.filter((slug) => offered.has(slug));
  const start = global.length >= 2 ? global : DEFAULT_SET;
  selected.value = start
    .filter((slug) => offered.has(slug))
    .slice(0, MAX_PARAMETERS);
}

function reload(): void {
  void load(params());
}

/** Settle the pollutants, then load: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  await settle();
  reload();
}

function onParameters(value: string[] | null): void {
  // past the cap, the last pick is dropped
  selected.value = (value || []).slice(0, MAX_PARAMETERS);
  reload();
}

function onMethod(value: Method): void {
  method.value = value;
  reload();
}

onMounted(() => void refresh());
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refresh());
});
</script>
