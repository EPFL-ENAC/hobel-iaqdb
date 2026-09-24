<template>
  <div>
    <div class="row items-center no-wrap q-mb-xs">
      <q-breadcrumbs class="text-caption" active-color="secondary" gutter="xs">
        <q-breadcrumbs-el
          v-for="(level, i) in levels"
          :key="i"
          :label="level.label"
          :class="i < levels.length - 1 ? 'cursor-pointer' : 'text-grey-8'"
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
        t('plots.no_data_for', {
          parameters: parameterLabels || t('plots.unknown').toLowerCase(),
        })
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
import { useExploreQuery } from '@/composables/useExploreQuery';
import type {
  ExploreBucket,
  ExploreDimension,
  ExploreEntity,
  ExploreParams,
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
  /** count only entities that contain the selected parameters */
  withParameters?: boolean;
  /** height of the plot area; the bars share it */
  height?: number;
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
}

const props = withDefaults(defineProps<Props>(), {
  withParameters: true,
  height: 200,
});
const { t } = useI18n();
const router = useRouter();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

const BAR_COLOR = '#4f8fcc';
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';

/** Drill stack, `stack[0]` being the chart as mounted. */
const stack = ref<Level[]>([]);
const current = computed(() => stack.value[stack.value.length - 1] ?? null);
const option = ref<EChartsOption>({});

const rootParams = computed<ExploreParams | null>(() => {
  void filtersStore.updates;
  const dimension = exploreStore.dimension(props.by);
  if (!dimension) return null;
  const params: ExploreParams = {
    entity: props.entity,
    by: [props.by],
    filter: exploreFilter(),
  };
  if (props.withParameters && exploreStore.parameters.length)
    params.parameters = [...exploreStore.parameters];
  return params;
});

// a filter or parameter change restarts the drill from the top
watch(
  rootParams,
  (params) => {
    const dimension = exploreStore.dimension(props.by);
    stack.value =
      params && dimension
        ? [{ params, dimension, label: dimension.label }]
        : [];
  },
  { immediate: true },
);

const { result, loading, error, empty } = useExploreQuery(
  'metadata',
  () => current.value?.params ?? null,
);

const levels = computed(() => stack.value);
/** false once the drill has reached `depth` levels below the first */
const canClick = computed(
  () => props.depth === undefined || stack.value.length - 1 < props.depth,
);

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
  const groups = te(key)
    ? t(key, buckets)
    : `${buckets} ${level.dimension.label.toLowerCase()}`;
  return `${entity} · ${groups}`;
});

function te(key: string): boolean {
  return t(key, 0) !== key;
}

function label(
  dimension: ExploreDimension,
  key: string | null | undefined,
): string {
  if (key === null || key === undefined) return t('plots.unknown');
  return dimension.key === 'study'
    ? exploreStore.studyName(key)
    : keyLabel(dimension.key, key);
}

watch(result, (value) => {
  if (value && current.value?.dimension.key === 'study') {
    void exploreStore.loadStudyNames(
      value.buckets.flatMap((bucket) => (bucket.key[0] ? [bucket.key[0]] : [])),
    );
  }
});

watch([result, () => exploreStore.studyNames], ([value]) => {
  const level = current.value;
  if (!value || !level) {
    option.value = {};
    return;
  }
  const items: BarItem[] = value.buckets.map((bucket) => ({
    name: label(level.dimension, bucket.key[0]),
    value: bucket.n,
    bucket,
  }));
  const entityWord = t(`${props.entity}_with_count`, 2).replace(/^\d+\s*/, '');
  option.value = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const item = (Array.isArray(params) ? params[0] : params)?.data as
          BarItem | undefined;
        return item
          ? `${item.name}<br/><b>${item.value}</b> ${entityWord}`
          : '';
      },
    },
    grid: { left: 8, right: 40, top: 8, bottom: 8, containLabel: true },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: items.map((item) => item.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: TEXT, width: 160, overflow: 'truncate' },
    },
    series: [
      {
        type: 'bar',
        data: items,
        barCategoryGap: '30%',
        cursor:
          canClick.value &&
          (level.dimension.drill_to || level.dimension.filter_path)
            ? 'pointer'
            : 'default',
        itemStyle: { color: BAR_COLOR, borderRadius: [0, 4, 4, 0] },
        emphasis: { itemStyle: { color: '#2f6fa8' } },
        label: { show: true, position: 'right', color: TEXT, formatter: '{c}' },
      },
    ],
  };
});

function onClick(event: { data?: unknown; componentType?: string }) {
  const level = current.value;
  const item = event.data as BarItem | undefined;
  if (!canClick.value || !level || !item || event.componentType !== 'series')
    return;
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
  stack.value = [...stack.value, { params: next, dimension, label: item.name }];
}

function popTo(index: number) {
  if (index < stack.value.length - 1)
    stack.value = stack.value.slice(0, index + 1);
}
</script>
