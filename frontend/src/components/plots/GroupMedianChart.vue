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
          v-for="(level, i) in stack"
          :key="i"
          :label="level.label"
          :class="i < stack.length - 1 ? 'cursor-pointer' : 'text-grey-8'"
          @click="popTo(i)"
        />
      </q-breadcrumbs>
      <q-space />
      <span v-if="summary" class="text-caption text-grey-7">{{ summary }}</span>
    </div>
    <div v-if="error" class="text-negative text-caption">
      {{ t('plots.error') }}: {{ error }}
    </div>
    <div
      v-else-if="empty || (result && !bars.length)"
      class="text-grey-7 text-caption"
    >
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
    <div v-if="dropped" class="text-caption text-grey-7 q-mt-xs">
      {{
        t('plots.unknown_left_out', {
          count: dropped.toLocaleString(locale),
          dimension: groupLabel.toLowerCase(),
        })
      }}
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
  initOptions,
  isUnknownKey,
  keyLabel,
  onBucketClick,
  updateOptions,
} from '@/components/plots/charts';
import { exploreRange } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';
import { useContextScope } from '@/composables/useContextScope';
import type {
  ExploreBucket,
  ExploreDimension,
  ExploreParams,
  ExploreStats,
} from '@/models';

use([SVGRenderer, BarChart, GridComponent, TooltipComponent]);

interface Props {
  /** dimension from /stats/schema the bars group by */
  by?: string;
  /** height of the plot area */
  height?: number;
  /** `vertical` (default): one column per group; `horizontal`: ranked rows, highest on top */
  orientation?: 'vertical' | 'horizontal';
}

interface Level {
  params: ExploreParams;
  dimension: ExploreDimension;
  label: string;
}

interface Bar {
  name: string;
  /** axis and summary label: the code of a "[Cfb] Temperate, …" name */
  short: string;
  value: number;
  stats: ExploreStats;
  bucket: ExploreBucket;
}

const props = withDefaults(defineProps<Props>(), {
  by: 'ventilation_type',
  height: 400,
  orientation: 'vertical',
});
const { t, locale } = useI18n();
const router = useRouter();
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
} = useContextScope({ exclude: [props.by], requireKnown: props.by });
/** Drill stack, `stack[0]` being the chart as mounted. */
const stack = ref<Level[]>([]);
const current = computed(() => stack.value[stack.value.length - 1] ?? null);

const { result, loading, error, empty, load } =
  useExploreRequest('measurements');

const unit = computed(() => result.value?.meta.unit || '');

function formatValue(value: number): string {
  return new Intl.NumberFormat(locale.value, {
    maximumFractionDigits: value < 10 ? 2 : 0,
  }).format(value);
}

/** label of the grouping of the first level, for the left-out note */
const groupLabel = computed(
  () => exploreStore.dimension(props.by)?.label || '',
);

/** "[Cfb] Temperate, no dry season, warm summer" → "Cfb"; other names as is */
function shortLabel(name: string): string {
  return /^\[([^\]]+)\]/.exec(name)?.[1] ?? name;
}

/** the dimension the loaded result groups by (it may lag the drill stack) */
const grouping = computed(() => result.value?.meta.dimensions[0] ?? '');

/** one bar per known group, highest median first */
const bars = computed<Bar[]>(() => {
  const dimension = grouping.value;
  return (result.value?.buckets || [])
    .flatMap((bucket) => {
      const key = bucket.key[0];
      if (isUnknownKey(key) || !bucket.stats) return [];
      return [
        {
          name: keyLabel(dimension, key as string),
          short: shortLabel(keyLabel(dimension, key as string)),
          value: bucket.stats.p50,
          stats: bucket.stats,
          bucket,
        },
      ];
    })
    .sort((a, b) => b.value - a.value);
});

/** daily values of the groups left out for lack of a known key */
const dropped = computed(() =>
  (result.value?.buckets || [])
    .filter((b) => isUnknownKey(b.key[0]))
    .reduce((sum, b) => sum + b.n, 0),
);

/** the highest group against the lowest, and how many groups compare */
const summary = computed(() => {
  const items = bars.value;
  if (!items.length) return '';
  const high = items[0] as Bar;
  const low = items[items.length - 1] as Bar;
  const u = unit.value ? ` ${unit.value}` : '';
  const groups = t(`plots.levels.${grouping.value}`, items.length);
  if (items.length < 2) return groups;
  return `${high.short} +${formatValue(high.value - low.value)}${u} · ${groups}`;
});

const option = computed<EChartsOption>(() => {
  const items = bars.value;
  if (!items.length) return {};
  const u = unit.value ? ` ${unit.value}` : '';
  const drills = !!current.value?.dimension.drill_to;
  const horizontal = props.orientation === 'horizontal';
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const bar = (Array.isArray(p) ? p[0] : p)?.data as Bar | undefined;
        if (!bar) return '';
        return [
          `<b>${bar.name}</b>`,
          `${t('plots.p50')}: <b>${formatValue(bar.stats.p50)}${u}</b>`,
          `${t('plots.iqr')}: ${formatValue(bar.stats.p25)} – ${formatValue(bar.stats.p75)}${u}`,
          `${t('plots.days')}: ${bar.bucket.n.toLocaleString(locale.value)}`,
        ].join('<br/>');
      },
    },
    grid: {
      left: 8,
      right: horizontal ? 48 : 8,
      top: 24,
      bottom: 8,
      containLabel: true,
    },
    // the groups on one axis, the medians on the other
    [horizontal ? 'yAxis' : 'xAxis']: {
      type: 'category',
      inverse: horizontal,
      data: items.map((bar) => bar.short),
      axisLine: { lineStyle: { color: GRID } },
      axisTick: { show: false },
      axisLabel: horizontal
        ? { color: TEXT, width: 160, overflow: 'truncate' }
        : { color: TEXT, interval: 0, width: 110, overflow: 'break' },
    },
    [horizontal ? 'xAxis' : 'yAxis']: {
      type: 'value',
      name: unit.value,
      nameTextStyle: { color: MUTED, align: horizontal ? 'left' : 'right' },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    series: [
      {
        type: 'bar',
        data: items,
        barCategoryGap: '30%',
        barMaxWidth: 96,
        cursor: drills ? 'pointer' : 'default',
        itemStyle: {
          color: BAR_COLOR,
          borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0],
        },
        label: {
          show: true,
          position: horizontal ? 'right' : 'top',
          color: TEXT,
          formatter: (p) => formatValue((p.data as Bar).value),
        },
      },
    ],
  };
});

/** Rebuild the first level from the menus and filters, and load it. */
function restart(): Promise<void> {
  const dimension = exploreStore.dimension(props.by);
  if (!dimension || !parameter.value) return show([]);
  const params: ExploreParams = {
    ...scopedFilter(),
    ...exploreRange(),
    agg: 'stats',
    by: [props.by],
    parameters: [parameter.value],
    grain: 'day',
  };
  return show([{ params, dimension, label: dimension.label }]);
}

/** Make `levels` the drill stack and load its last level. */
async function show(levels: Level[]): Promise<void> {
  stack.value = levels;
  await load(current.value?.params ?? null);
}

/** Settle the menus, then restart: on mount and when the filters are applied. */
async function refreshAll(): Promise<void> {
  await refresh();
  await restart();
}

async function onParameter(value: string | null): Promise<void> {
  await selectParameter(value);
  await restart();
}

async function onContext(value: string | null): Promise<void> {
  // the bars change only if a value of the old context was narrowing them
  const narrowed = contextValue.value !== null;
  await selectContext(value);
  if (narrowed) await restart();
}

function onValue(value: string | null): void {
  selectValue(value);
  void restart();
}

onMounted(() => void refreshAll());
// applying the filters restarts the drill from the top
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refreshAll());
});

/** a click on a bar drills into the next level, e.g. space types */
function onClick(event: { data?: unknown }) {
  const level = current.value;
  const bar = event.data as Bar | undefined;
  if (!level?.dimension.drill_to || !bar) return;
  const next = onBucketClick(
    { kind: 'drill', dimension: level.dimension, params: level.params, router },
    bar.bucket,
  );
  const dimension = exploreStore.dimension(next?.by?.[0] || '');
  if (!next || !dimension) return;
  void show([...stack.value, { params: next, dimension, label: bar.name }]);
}

function popTo(index: number) {
  if (index < stack.value.length - 1)
    void show(stack.value.slice(0, index + 1));
}
</script>
