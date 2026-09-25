<template>
  <div>
    <div class="row items-center q-col-gutter-sm q-mb-sm">
      <div class="col-12 col-sm-4">
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
      <div class="col-6 col-sm-4">
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
      <div class="col-6 col-sm-4">
        <q-select
          :model-value="contextValue"
          :options="valueOptions"
          :label="contextLabel"
          :disable="!context"
          :loading="valuesLoading"
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onValue"
        />
      </div>
    </div>
    <div class="row items-center no-wrap q-mb-xs">
      <q-breadcrumbs class="text-caption" active-color="secondary" gutter="xs">
        <q-breadcrumbs-el
          :label="t('plots.month_of_year')"
          :class="period ? 'cursor-pointer' : 'text-grey-8'"
          @click="period = null"
        />
        <q-breadcrumbs-el
          v-if="period"
          :label="period.label"
          class="text-grey-8"
        />
      </q-breadcrumbs>
      <q-space />
      <span v-if="summary" class="text-caption text-grey-7">{{ summary }}</span>
      <q-badge
        v-if="benchmark?.placeholder"
        color="orange-7"
        :label="t('plots.placeholder')"
        class="q-ml-xs"
      />
    </div>
    <div v-if="error" class="text-negative text-caption">
      {{ t('plots.error') }}: {{ error }}
    </div>
    <div v-else-if="!benchmark" class="text-grey-7 text-caption">
      {{ t('plots.no_benchmark', { parameter: parameterLabel }) }}
    </div>
    <div v-else-if="empty" class="text-grey-7 text-caption">
      {{ t('plots.no_data_for', { parameters: parameterLabel }) }}
    </div>
    <div v-else :style="`height: ${height}px;`">
      <e-charts
        autoresize
        :init-options="initOptions"
        :option="option"
        :update-options="updateOptions"
        :loading="loading"
        @click="onClick"
      />
    </div>
    <div v-if="benchmarkLabel" class="text-caption text-grey-7 q-mt-xs">
      {{ benchmarkLabel }}
    </div>
  </div>
</template>

<script setup lang="ts">
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, TooltipComponent } from 'echarts/components';
import {
  benchmarkOf,
  initOptions,
  updateOptions,
} from '@/components/plots/charts';
import { exploreRange } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';
import { useContextScope } from '@/composables/useContextScope';
import type { ExploreParams } from '@/models';

use([SVGRenderer, BarChart, GridComponent, TooltipComponent]);

interface Props {
  /** height of the plot area */
  height?: number;
}

/** A calendar month, 1 = January. */
interface Period {
  label: string;
  month: number;
}

interface Bar {
  name: string;
  value: number;
  above: number;
  total: number;
  /** the period this bar drills into, at the top level */
  period: Period | null;
}

withDefaults(defineProps<Props>(), { height: 400 });
const { t, locale } = useI18n();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const BAR_COLOR = '#2f5596';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';

const {
  parameter,
  parameterOptions,
  parameterLabel,
  context,
  contextValue,
  contextOptions,
  contextLabel,
  valueOptions,
  valuesLoading,
  scopedFilter,
  refresh,
  selectParameter,
  selectContext,
  selectValue,
} = useContextScope({ withBenchmark: true });
/** the period drilled into, shown year by year; null at the top level */
const period = ref<Period | null>(null);

const { result, loading, error, empty, load } =
  useExploreRequest('measurements');

const benchmark = computed(() =>
  benchmarkOf(exploreStore.schema, parameter.value),
);

const benchmarkLabel = computed(() => {
  const b = benchmark.value;
  if (!b) return '';
  const note = b.note ? ` (${b.note})` : '';
  return t('plots.share_above_hint', {
    benchmark: `${b.source} · ${formatValue(b.value)} ${b.unit}${note}`,
    periods: t(`plots.averaging_${b.averaging}`),
  });
});

const periods = computed<Period[]>(() => {
  const format = new Intl.DateTimeFormat(locale.value, {
    month: 'short',
    timeZone: 'UTC',
  });
  return Array.from({ length: 12 }, (_, i) => ({
    label: format.format(new Date(Date.UTC(2000, i, 1))),
    month: i + 1,
  }));
});

function formatValue(value: number): string {
  return new Intl.NumberFormat(locale.value, {
    maximumFractionDigits: value < 10 ? 2 : 0,
  }).format(value);
}

function formatShare(value: number): string {
  return `${Math.round(value * 100)}%`;
}

/** days (or hours) above and in total, per calendar month and year */
const cells = computed(() =>
  (result.value?.buckets || []).flatMap((b) => {
    const [month, year] = b.key;
    if (!month || !year || !b.exceedance) return [];
    return [
      {
        month: Number(month),
        year: new Date(year).getUTCFullYear(),
        above: b.exceedance.n_above,
        total: b.n,
      },
    ];
  }),
);

/** one bar per period, or per year within the drilled period */
const bars = computed<Bar[]>(() => {
  const drilled = period.value;
  if (drilled) {
    const byYear = new Map<number, { above: number; total: number }>();
    for (const c of cells.value) {
      if (c.month !== drilled.month) continue;
      const sum = byYear.get(c.year) ?? { above: 0, total: 0 };
      sum.above += c.above;
      sum.total += c.total;
      byYear.set(c.year, sum);
    }
    return [...byYear.entries()]
      .sort(([a], [b]) => a - b)
      .map(([year, sum]) => toBar(String(year), sum, null));
  }
  return periods.value.map((p) => {
    const sum = { above: 0, total: 0 };
    for (const c of cells.value)
      if (c.month === p.month) {
        sum.above += c.above;
        sum.total += c.total;
      }
    return toBar(p.label, sum, p);
  });
});

function toBar(
  name: string,
  sum: { above: number; total: number },
  drillsInto: Period | null,
): Bar {
  return {
    name,
    value: sum.total ? sum.above / sum.total : 0,
    above: sum.above,
    total: sum.total,
    period: drillsInto,
  };
}

/** highest and lowest share among the periods with data */
const summary = computed(() => {
  const items = bars.value.filter((bar) => bar.total > 0);
  if (!items.length) return '';
  const high = items.reduce((a, b) => (b.value > a.value ? b : a));
  const low = items.reduce((a, b) => (b.value < a.value ? b : a));
  return `${high.name} ${formatShare(high.value)} · ${low.name} ${formatShare(low.value)}`;
});

function params(): ExploreParams | null {
  const b = benchmark.value;
  if (!parameter.value || !b || !exploreStore.dimension('month_of_year'))
    return null;
  return {
    ...scopedFilter(),
    ...exploreRange(),
    agg: 'exceedance',
    by: ['month_of_year', 'year'],
    parameters: [parameter.value],
    threshold: b.value,
    // "days above" counts days for a 24 h guideline, hours for an 8 h one
    grain: b.averaging,
  };
}

function reload() {
  period.value = null;
  void load(params());
}

/** Settle the menus, then reload: on mount and when the filters are applied. */
async function refreshAll(): Promise<void> {
  await refresh();
  reload();
}

async function onParameter(value: string | null): Promise<void> {
  await selectParameter(value);
  reload();
}

async function onContext(value: string | null): Promise<void> {
  // the bars change only if a value of the old context was narrowing them
  const narrowed = contextValue.value !== null;
  await selectContext(value);
  if (narrowed) reload();
}

function onValue(value: string | null): void {
  selectValue(value);
  reload();
}

onMounted(() => void refreshAll());
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refreshAll());
});

const option = computed<EChartsOption>(() => {
  const items = bars.value;
  if (!items.length) {
    return {};
  }
  const b = benchmark.value;
  const unit = b ? t(`plots.averaging_${b.averaging}`) : '';
  const drills = !period.value;
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const bar = (Array.isArray(p) ? p[0] : p)?.data as Bar | undefined;
        if (!bar) return '';
        return [
          `<b>${bar.name}</b>`,
          `${t('plots.share_above')}: <b>${formatShare(bar.value)}</b>`,
          t('plots.above_of_total', {
            above: bar.above.toLocaleString(locale.value),
            total: bar.total.toLocaleString(locale.value),
            unit,
          }),
        ].join('<br/>');
      },
    },
    grid: { left: 8, right: 8, top: 24, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      data: items.map((bar) => bar.name),
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel: { color: TEXT },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: (extent: { max: number }) =>
        Math.min(1, Math.ceil((extent.max || 0.1) * 10) / 10),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED, formatter: (v: number) => formatShare(v) },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: [
      {
        type: 'bar',
        data: items,
        barCategoryGap: '30%',
        cursor: drills ? 'pointer' : 'default',
        itemStyle: { color: BAR_COLOR, borderRadius: [4, 4, 0, 0] },
        label: {
          show: true,
          position: 'top',
          color: TEXT,
          formatter: (p) => {
            const bar = p.data as Bar;
            return bar.total ? formatShare(bar.value) : '';
          },
        },
      },
    ],
  };
});

/** a click on a month shows it year by year */
function onClick(event: { data?: unknown }) {
  const bar = event.data as Bar | undefined;
  if (bar?.period && bar.total) period.value = bar.period;
}
</script>
