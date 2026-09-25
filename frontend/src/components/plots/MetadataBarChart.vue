<template>
  <div>
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
    <div v-else-if="empty" class="text-grey-7 text-caption">
      {{
        parameterLabels
          ? t('plots.no_data_for', { parameters: parameterLabels })
          : t('plots.no_data')
      }}
      <span v-if="availableLabels">{{
        t('plots.available_parameters', { parameters: availableLabels })
      }}</span>
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
  keyLabel,
  onBucketClick,
  updateOptions,
} from '@/components/plots/charts';
import { exploreFilter } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type {
  ExploreBucket,
  ExploreDimension,
  ExploreEntity,
  ExploreParams,
  ExploreResult,
} from '@/models';

use([SVGRenderer, BarChart, GridComponent, TooltipComponent]);

interface Props {
  /** catalog entity counted per key */
  entity: ExploreEntity;
  /** dimension key from /stats/schema the chart opens on */
  by: string;
  /**
   * Dimension at which a click stops drilling and navigates to the bucket's
   * catalog view; by default the chart drills as long as the dimension has a
   * `drill_to`.
   */
  leaf?: string;
  /** how many levels a click may drill below the first; unlimited by default */
  depth?: number;
  /**
   * `drill` (default): a click refines the chart itself, level by level;
   * `filter`: a click pushes the bucket key into the global filters, so the
   * map, the lists and every chart re-query. The keys already selected in the
   * global filters are highlighted; `none`: the chart is read-only.
   */
  click?: 'drill' | 'filter' | 'none';
  /** count only entities that contain the selected parameters */
  withParameters?: boolean;
  /** height of the plot area; the bars share it */
  height?: number;
  /** `horizontal` (default): one row per key; `vertical`: one column per key */
  orientation?: 'horizontal' | 'vertical';
}

interface Level {
  params: ExploreParams;
  dimension: ExploreDimension;
  label: string;
}

interface BarItem {
  name: string;
  value: number;
  bucket: ExploreBucket;
  itemStyle: { color: string };
}

const props = withDefaults(defineProps<Props>(), {
  withParameters: true,
  height: 200,
  click: 'drill',
  orientation: 'horizontal',
});
const i18n = useI18n();
const { t } = i18n;
const router = useRouter();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const BAR_COLOR = '#4f8fcc';
const SELECTED_COLOR = '#2f6fa8';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';
/** above this many columns, vertical bars slant their labels */
const VERTICAL_FLAT_MAX = 6;

/** Drill stack, `stack[0]` being the chart as mounted. */
const stack = ref<Level[]>([]);
const current = computed(() => stack.value[stack.value.length - 1] ?? null);
const option = ref<EChartsOption>({});

const { result, loading, error, empty, load } = useExploreRequest('metadata');

/** false once the drill has reached `depth` levels below the first */
const canClick = computed(
  () => props.depth === undefined || stack.value.length - 1 < props.depth,
);

/** whether a click on the current level does anything */
const clickable = computed(() => {
  const dimension = current.value?.dimension;
  if (!dimension || props.click === 'none') return false;
  if (props.click === 'filter') return !!dimension.filter_path;
  return canClick.value && !!(dimension.drill_to || dimension.filter_path);
});

/** In `filter` mode, the keys of this dimension already in the global filters. */
const selectedKeys = computed<Set<string>>(() => {
  void filtersStore.updates;
  if (props.click !== 'filter') return new Set();
  const path = current.value?.dimension.filter_path;
  const selected: Record<string, string[]> = {
    '$building.country': filtersStore.countries,
    '$building.city': filtersStore.cities,
    '$building.climate_zone': filtersStore.climate_zones,
    '$building.type': filtersStore.building_types,
    '$space.mechanical_ventilation_type': filtersStore.mechanical_ventilation_types,
  };
  return new Set(path ? selected[path] || [] : []);
});

const parameterLabels = computed(() =>
  exploreStore.parameters.map(exploreStore.parameterLabel).join(', '),
);

const availableLabels = computed(() =>
  (result.value?.meta.available_parameters || [])
    .map(exploreStore.parameterLabel)
    .join(', '),
);

const summary = computed(() => {
  const value = result.value;
  const level = current.value;
  if (!value || !level || value.meta.n === 0) return '';
  const entity = t(`${props.entity}_with_count`, value.meta.n);
  const key = `plots.levels.${level.dimension.key}`;
  const buckets = value.buckets.length;
  const groups = i18n.te(key)
    ? t(key, buckets)
    : `${buckets} ${level.dimension.label.toLowerCase()}`;
  return `${entity} · ${groups}`;
});

onMounted(() => void restart());
// applying the filters (or the parameters) restarts the drill from the top
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void restart());
});

/** Rebuild the first level from the current filters and load it. */
function restart(): Promise<void> {
  const dimension = exploreStore.dimension(props.by);
  if (!dimension) return show([]);
  const params: ExploreParams = {
    entity: props.entity,
    by: [props.by],
    filter: exploreFilter(),
  };
  if (props.withParameters && exploreStore.parameters.length)
    params.parameters = [...exploreStore.parameters];
  return show([{ params, dimension, label: dimension.label }]);
}

/** Make `levels` the drill stack and load its last level. */
async function show(levels: Level[]): Promise<void> {
  stack.value = levels;
  const level = current.value;
  const value = await load(level?.params ?? null);
  // a later show() took over while this one waited
  if (current.value !== level) return;
  if (!value || !level) {
    option.value = {};
    return;
  }
  option.value = buildOption(level, value);
}

function label(
  dimension: ExploreDimension,
  key: string | null | undefined,
): string {
  if (key === null || key === undefined) return t('plots.unknown');
  return keyLabel(dimension.key, key);
}

function buildOption(level: Level, value: ExploreResult): EChartsOption {
  const items: BarItem[] = value.buckets.map((bucket) => ({
    name: label(level.dimension, bucket.key[0]),
    value: bucket.n,
    bucket,
    itemStyle: {
      color:
        bucket.key[0] && selectedKeys.value.has(bucket.key[0])
          ? SELECTED_COLOR
          : BAR_COLOR,
    },
  }));
  const countKey = `${props.entity}_with_count`;
  const vertical = props.orientation === 'vertical';
  const valueAxis = {
    type: 'value' as const,
    minInterval: 1,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: MUTED },
    splitLine: { lineStyle: { color: GRID, width: 1 } },
  };
  const categoryAxis = {
    type: 'category' as const,
    // horizontal bars read top-down in bucket order
    inverse: !vertical,
    data: items.map((item) => item.name),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: !vertical
      ? { color: TEXT, width: 160, overflow: 'truncate' as const }
      : items.length > VERTICAL_FLAT_MAX
        ? // too many columns for flat labels: slant and truncate them
          { color: TEXT, interval: 0, rotate: 40, width: 120, overflow: 'truncate' as const }
        : { color: TEXT, interval: 0, width: 100, overflow: 'break' as const },
  };
  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const item = (Array.isArray(params) ? params[0] : params)?.data as
          BarItem | undefined;
        return item
          ? `${item.name}<br/>${t(countKey, item.value)}`
          : '';
      },
    },
    grid: vertical
      ? { left: 8, right: 8, top: 24, bottom: 8, containLabel: true }
      : { left: 8, right: 40, top: 8, bottom: 8, containLabel: true },
    xAxis: vertical ? categoryAxis : valueAxis,
    yAxis: vertical ? valueAxis : categoryAxis,
    series: [
      {
        type: 'bar',
        data: items,
        barCategoryGap: '30%',
        cursor: clickable.value ? 'pointer' : 'default',
        itemStyle: { borderRadius: vertical ? [4, 4, 0, 0] : [0, 4, 4, 0] },
        emphasis: { itemStyle: { color: SELECTED_COLOR } },
        label: {
          show: true,
          position: vertical ? 'top' : 'right',
          color: TEXT,
          formatter: '{c}',
        },
      },
    ],
  };
}

function onClick(event: { data?: unknown; componentType?: string }) {
  const level = current.value;
  const item = event.data as BarItem | undefined;
  if (!clickable.value || !level || !item || event.componentType !== 'series')
    return;
  if (props.click === 'filter') {
    // the filters store bumps `updates`, which restarts the chart from the root
    onBucketClick(
      { kind: 'filter', dimension: level.dimension, params: level.params },
      item.bucket,
    );
    return;
  }
  const drills =
    level.dimension.drill_to !== null && level.dimension.key !== props.leaf;
  const next = onBucketClick(
    {
      kind: drills ? 'drill' : 'navigate',
      dimension: level.dimension,
      params: level.params,
      router,
    },
    item.bucket,
  );
  if (!next) return;
  const dimension = exploreStore.dimension(next.by?.[0] || '');
  if (!dimension) return;
  void show([...stack.value, { params: next, dimension, label: item.name }]);
}

function popTo(index: number) {
  if (index < stack.value.length - 1) void show(stack.value.slice(0, index + 1));
}
</script>
