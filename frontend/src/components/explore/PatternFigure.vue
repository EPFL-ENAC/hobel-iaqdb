<template>
  <ChartCard :eyebrow="eyebrow" :title="title" :footer-blank="!drilled && !hint">
    <template #actions>
      <FigureMenu
        v-if="parameterOptions.length > 1"
        :label="t('explore_figures.pattern.pollutant')"
        :model-value="parameter"
        :options="parameterOptions"
        @update:model-value="onParameter"
      />
      <FigureMenu
        :label="t('explore_figures.pattern.year')"
        :model-value="year"
        :options="yearOptions"
        @update:model-value="onYear"
      />
    </template>
    <FigureFrame :height="height" :loading="loading" :error="error" :empty="emptyMessage">
      <e-charts
        autoresize
        :init-options="initOptions"
        :option="option"
        :update-options="updateOptions"
        @click="onClick"
      />
    </FigureFrame>
    <template #footer>
      <button v-if="drilled" type="button" class="figure-link" @click="popTo(0)">
        <q-icon name="arrow_back" size="14px" class="q-mr-xs" />{{ t('explore_figures.pattern.back', { year }) }}
      </button>
      <span v-if="hint" class="pattern-figure__hint">
        <q-icon name="ads_click" size="16px" class="q-mr-xs" />{{ hint }}
      </span>
    </template>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * A pollutant through one year: the monthly median and its middle half
 * against the reference, and under it the share of periods above the
 * reference; a click on a month shows its days.
 */
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { BarChart, LineChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, MarkLineComponent, TitleComponent, TooltipComponent } from 'echarts/components';
import ChartCard from '@/components/explore/ChartCard.vue';
import FigureFrame from '@/components/explore/FigureFrame.vue';
import FigureMenu from '@/components/explore/FigureMenu.vue';
import {
  FIGURE_ACCENT,
  FIGURE_GAP,
  GRID,
  MUTED,
  benchmarkOf,
  initOptions,
  niceTicks,
  updateOptions,
} from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useParameterChoice } from '@/composables/useContextScope';
import { useDrillStack } from '@/composables/useDrillStack';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type { ExploreParams, ExploreResult, ExploreStats } from '@/models';

use([SVGRenderer, LineChart, BarChart, GridComponent, MarkLineComponent, TitleComponent, TooltipComponent]);

interface Props {
  eyebrow: string;
  title: string;
  /** height of the plot area: the levels, then the shares under them */
  height?: number;
}

/** The year by month, or a month by day: the levels and the shares above the reference. */
interface Level {
  stats: ExploreParams;
  exceedance: ExploreParams;
  /** `month` or `day` */
  by: string;
  from: string;
  to: string;
}

interface Loaded {
  stats: ExploreResult;
  exceedance: ExploreResult | null;
}

/** a period of the level, with what it has */
interface Slot {
  key: string;
  label: string;
  stats: ExploreStats | null;
  /** 0..1 of the periods above the reference */
  above: number | null;
}

withDefaults(defineProps<Props>(), { height: 380 });
const { t, locale } = useI18n();
const { formatValue, formatShare, describeReference } = useChartFormat();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

/** the levels' grid, then the shares' grid under it, in pixels from the top */
const LEVELS = { top: 12, height: 200 };
const SHARES = { top: 268, height: 72 };
const LEFT = 48;

const parameters = useParameterChoice({ withBenchmark: true });
const { parameter, parameterOptions, noDataMessage } = parameters;
const year = ref<number | null>(null);
const slots = ref<Slot[]>([]);

const yearsRequest = useExploreRequest('measurements');
const statsRequest = useExploreRequest('measurements');
const exceedanceRequest = useExploreRequest('measurements');

const { stack, current, show, popTo } = useDrillStack<Level, Loaded>({
  fetch: loadLevel,
  paint: (level, loaded) => (slots.value = toSlots(level, loaded)),
  clear: () => (slots.value = []),
});

const benchmark = computed(() => benchmarkOf(exploreStore.schema, parameter.value));
const drilled = computed(() => stack.value.length > 1);
const byMonth = computed(() => current.value?.by === 'month');

const loading = computed(
  () => yearsRequest.loading.value || statsRequest.loading.value || exceedanceRequest.loading.value,
);
/** without its years, the figure cannot pick one to show */
const error = computed(() => statsRequest.error.value || yearsRequest.error.value);
const emptyMessage = computed(() => {
  if (!parameter.value || !benchmark.value || year.value === null) return noDataMessage.value;
  return statsRequest.empty.value ? noDataMessage.value : '';
});

const hint = computed(() => (byMonth.value && slots.value.length ? t('explore_figures.hint_drill') : ''));

const yearOptions = computed(() =>
  (yearsRequest.result.value?.buckets || [])
    .flatMap((b) => (b.key[0] ? [Number(b.key[0].slice(0, 4))] : []))
    .sort((a, b) => b - a)
    .map((y) => ({ value: y, label: String(y) })),
);

/** Settle the pollutant, then the year, then load: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  await parameters.refresh();
  await reloadYears();
}

async function onParameter(value: string | null): Promise<void> {
  parameter.value = value;
  await reloadYears();
}

function onYear(value: number | null): void {
  year.value = value;
  void restart();
}

onMounted(() => void refresh());
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refresh());
});

/** The years with data for the pollutant: keeps the year if still offered, else the busiest. */
async function reloadYears(): Promise<void> {
  if (!parameter.value) {
    await yearsRequest.load(null);
    year.value = null;
    return restart();
  }
  const value = await yearsRequest.load({
    filter: exploreFilter(),
    ...exploreRange(),
    agg: 'count',
    by: ['year'],
    parameters: [parameter.value],
    grain: 'day',
  });
  if (!value) return;
  const years = value.buckets.flatMap((b) => (b.key[0] ? [{ year: Number(b.key[0].slice(0, 4)), n: b.n }] : []));
  if (year.value === null || !years.some((y) => y.year === year.value))
    year.value = years.reduce<{ year: number; n: number } | null>((best, y) => (!best || y.n > best.n ? y : best), null)?.year ?? null;
  return restart();
}

/** The requests of one period, by month or by day. */
function levelOf(by: 'month' | 'day', from: string, to: string): Level | null {
  const b = benchmark.value;
  if (!parameter.value || !b) return null;
  const base: ExploreParams = {
    filter: exploreFilter(),
    by: [by],
    parameters: [parameter.value],
    from,
    to,
  };
  return {
    // levels as daily means for one space; the shares at the reference's own averaging
    stats: { ...base, agg: 'stats', grain: 'day' },
    exceedance: { ...base, agg: 'exceedance', grain: b.averaging, threshold: b.value },
    by,
    from,
    to,
  };
}

/** Rebuild the year level and load it. */
function restart(): Promise<void> {
  if (year.value === null) return show([]);
  const level = levelOf('month', `${year.value}-01-01`, `${year.value + 1}-01-01`);
  return show(level ? [level] : []);
}

async function loadLevel(level: Level | null): Promise<Loaded | null> {
  const [stats, exceedance] = await Promise.all([
    statsRequest.load(level?.stats ?? null),
    exceedanceRequest.load(level?.exceedance ?? null),
  ]);
  return stats ? { stats, exceedance } : null;
}

/** every period of the level, gaps included */
function toSlots(level: Level, { stats, exceedance }: Loaded): Slot[] {
  const levels = new Map(stats.buckets.flatMap((b) => (b.key[0] && b.stats ? [[b.key[0].slice(0, 10), b.stats] as const] : [])));
  const shares = new Map(
    (exceedance?.buckets || []).flatMap((b) =>
      b.key[0] && b.exceedance ? [[b.key[0].slice(0, 10), b.exceedance.share] as const] : [],
    ),
  );
  const format = new Intl.DateTimeFormat(
    locale.value,
    level.by === 'month' ? { month: 'short', timeZone: 'UTC' } : { day: 'numeric', timeZone: 'UTC' },
  );
  const out: Slot[] = [];
  const end = new Date(`${level.to}T00:00:00Z`);
  for (const date = new Date(`${level.from}T00:00:00Z`); date < end; ) {
    const key = date.toISOString().slice(0, 10);
    out.push({ key, label: format.format(date), stats: levels.get(key) ?? null, above: shares.get(key) ?? null });
    if (level.by === 'month') date.setUTCMonth(date.getUTCMonth() + 1);
    else date.setUTCDate(date.getUTCDate() + 1);
  }
  return out;
}

const unit = computed(() => statsRequest.result.value?.meta.unit || benchmark.value?.unit || '');

const referenceText = computed(() => (benchmark.value ? describeReference(benchmark.value) : ''));

const option = computed<EChartsOption>(() => {
  const items = slots.value;
  const b = benchmark.value;
  if (!items.length || !b) return {};
  const u = unit.value ? ` ${unit.value}` : '';
  const values = items.flatMap((s) => (s.stats ? [s.stats.p25, s.stats.p75] : []));
  const ticks = niceTicks(Math.min(...values, b.value), Math.max(...values, b.value), 4);
  const low = ticks[0] ?? 0;
  const high = ticks[ticks.length - 1] ?? 1;
  const labels = items.map((s) => s.label);
  const periods = t(`explore_figures.distribution.periods.${b.averaging}`);
  const axisLabel = { color: MUTED, fontSize: 11 };
  return {
    title: {
      text: t('explore_figures.pattern.share_above', { periods, value: referenceText.value }).toUpperCase(),
      left: LEFT,
      top: SHARES.top - 34,
      textStyle: { color: MUTED, fontSize: 11, fontWeight: 'normal' },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(0, 0, 0, 0.04)' } },
      formatter: (params) => {
        const first = Array.isArray(params) ? params[0] : params;
        const slot = first ? items[first.dataIndex] : undefined;
        if (!slot) return '';
        const lines = [`<b>${slot.label}${byMonth.value ? '' : ` ${current.value?.from.slice(0, 7) ?? ''}`}</b>`];
        if (slot.stats) {
          lines.push(`${t('explore_figures.pattern.median')}: <b>${formatValue(slot.stats.p50)}${u}</b>`);
          lines.push(
            `${t('explore_figures.pattern.middle')}: ${formatValue(slot.stats.p25)} – ${formatValue(slot.stats.p75)}${u}`,
          );
        }
        if (slot.above !== null)
          lines.push(t('explore_figures.pattern.tip_above', { share: formatShare(slot.above), periods, value: referenceText.value }));
        return lines.length > 1 ? lines.join('<br/>') : '';
      },
    },
    grid: [
      { left: LEFT, right: 16, top: LEVELS.top, height: LEVELS.height },
      { left: LEFT, right: 16, top: SHARES.top, height: SHARES.height },
    ],
    xAxis: [
      {
        type: 'category',
        gridIndex: 0,
        data: labels,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
      },
      {
        type: 'category',
        gridIndex: 1,
        data: labels,
        axisLine: { lineStyle: { color: GRID } },
        axisTick: { show: false },
        axisLabel,
      },
    ],
    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        min: low,
        max: high,
        interval: (ticks[1] ?? high) - low,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { ...axisLabel, formatter: (v: number) => formatValue(v) },
        splitLine: { lineStyle: { color: GRID, width: 1 } },
      },
      {
        type: 'value',
        gridIndex: 1,
        min: 0,
        // the tallest bar fills the strip, its label above it
        max: (extent: { max: number }) => Math.max(extent.max, 0.01) * 1.35,
        show: false,
      },
    ],
    series: [
      {
        // the band's floor, stacked under it, not drawn
        type: 'line',
        stack: 'band',
        data: items.map((s) => s.stats?.p25 ?? '-'),
        lineStyle: { opacity: 0 },
        symbol: 'none',
        silent: true,
        tooltip: { show: false },
      },
      {
        type: 'line',
        stack: 'band',
        data: items.map((s) => (s.stats ? s.stats.p75 - s.stats.p25 : '-')),
        lineStyle: { opacity: 0 },
        symbol: 'none',
        areaStyle: { color: 'rgba(74, 163, 154, 0.18)' },
        silent: true,
      },
      {
        type: 'line',
        data: items.map((s) => s.stats?.p50 ?? '-'),
        connectNulls: false,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: FIGURE_ACCENT, width: 1.5 },
        itemStyle: { color: 'white', borderColor: FIGURE_ACCENT, borderWidth: 1.5 },
        cursor: byMonth.value ? 'pointer' : 'default',
        // the reference's label sits above the line: not cut at the grid's edge
        clip: false,
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: FIGURE_GAP, type: 'solid', width: 1.5 },
          label: {
            position: 'insideEndTop',
            distance: 6,
            padding: [2, 0, 4, 0],
            lineHeight: 16,
            color: FIGURE_GAP,
            fontSize: 11,
            formatter: t('explore_figures.pattern.reference', { value: referenceText.value }),
          },
          data: [{ yAxis: b.value }],
        },
      },
      {
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: items.map((s) => s.above ?? '-'),
        barCategoryGap: '40%',
        itemStyle: { color: FIGURE_ACCENT },
        cursor: byMonth.value ? 'pointer' : 'default',
        label: {
          show: true,
          position: 'top',
          color: MUTED,
          fontSize: 11,
          formatter: (p: { value: unknown }) => (typeof p.value === 'number' ? formatShare(p.value) : ''),
        },
      },
    ],
  };
});

/** a click on a month, its point or its bar, shows its days */
function onClick(event: { componentType?: string; dataIndex?: number }): void {
  const level = current.value;
  if (!level || level.by !== 'month' || event.componentType !== 'series' || event.dataIndex === undefined) return;
  const slot = slots.value[event.dataIndex];
  if (!slot?.stats) return;
  const from = new Date(`${slot.key}T00:00:00Z`);
  const to = new Date(from);
  to.setUTCMonth(to.getUTCMonth() + 1);
  const next = levelOf('day', slot.key, to.toISOString().slice(0, 10));
  if (next) void show([...stack.value, next]);
}
</script>

<style scoped lang="scss">
.pattern-figure__hint {
  margin-left: auto;
  color: $grey-9;
}
</style>
