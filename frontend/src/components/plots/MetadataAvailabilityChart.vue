<template>
  <div>
    <div class="row items-center q-col-gutter-sm q-mb-sm">
      <div class="col-6 col-sm-4">
        <q-select
          :model-value="entity"
          :options="entityOptions"
          :label="t('plots.entity')"
          emit-value
          map-options
          dense
          outlined
          @update:model-value="onEntity"
        />
      </div>
    </div>
    <div class="row items-center no-wrap q-mb-xs">
      <span class="text-caption text-grey-8">{{
        t('plots.field_availability')
      }}</span>
      <q-space />
      <span v-if="summary" class="text-caption text-grey-7">{{ summary }}</span>
    </div>
    <div v-if="error" class="text-negative text-caption">
      {{ t('plots.error') }}: {{ error }}
    </div>
    <div v-else-if="empty" class="text-grey-7 text-caption">
      {{ t('plots.no_data') }}
    </div>
    <template v-else>
      <div :style="`height: ${height}px;`">
        <e-charts
          autoresize
          :init-options="initOptions"
          :option="option"
          :update-options="updateOptions"
          :loading="loading"
        />
      </div>
      <div
        class="row items-center q-gutter-md q-mt-xs text-caption text-grey-8"
      >
        <div
          v-for="band in BANDS"
          :key="band.key"
          class="row items-center no-wrap"
        >
          <span class="band-dot q-mr-xs" :style="`background: ${band.color}`" />
          {{ t(`plots.quality.${band.key}`) }}
        </div>
      </div>
      <div v-if="neverFilled.length" class="text-caption text-grey-7 q-mt-xs">
        {{ t('plots.never_filled', { fields: neverFilled.join(', ') }) }}
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, TooltipComponent } from 'echarts/components';
import { initOptions, updateOptions } from '@/components/plots/charts';
import { exploreFilter } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type { ExploreEntity } from '@/models';

use([SVGRenderer, BarChart, GridComponent, TooltipComponent]);

interface Props {
  /** height of the plot area; the bars share it */
  height?: number;
}

interface Bar {
  name: string;
  value: number;
  present: number;
  total: number;
  itemStyle: { color: string };
  band: string;
}

withDefaults(defineProps<Props>(), { height: 400 });
const i18n = useI18n();
const { t, locale } = i18n;
const filtersStore = useFiltersStore();

/** quality of a field by its share filled in, best first */
const GAP = { key: 'gap', min: 0, color: '#c05b7b' };
const BANDS = [
  { key: 'strong', min: 0.8, color: '#2f5596' },
  { key: 'review', min: 0.7, color: '#e8a33d' },
  GAP,
];
const TEXT = '#424242';
const MUTED = '#757575';
const GRID = '#e0e0e0';
/** where each entity's field labels live in the i18n messages */
const LABELS: Record<string, string> = {
  studies: 'study',
  buildings: 'study.building',
  spaces: 'study.space',
};

const entity = ref<ExploreEntity>('buildings');

const { result, loading, error, empty, load } = useExploreRequest('metadata');

const entityOptions = computed(() => [
  { value: 'studies', label: t('plots.entities.studies') },
  { value: 'buildings', label: t('plots.entities.buildings') },
  { value: 'spaces', label: t('plots.entities.spaces') },
]);

function fieldLabel(field: string): string {
  const path = `${LABELS[entity.value]}.${field}`;
  if (i18n.te(path)) return t(path);
  const words = field.replace(/_/g, ' ');
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** whole percents, as labels show them; a trace stays visible as "< 1%" */
function formatShare(value: number): string {
  if (value > 0 && value < 0.005) return '< 1%';
  return `${Math.round(value * 100)}%`;
}

interface Band {
  key: string;
  min: number;
  color: string;
}

/** the best band a share reaches, on the rounded percent the label shows */
function bandOf(share: number): Band {
  const shown = Math.round(share * 100) / 100;
  for (const band of BANDS) if (shown >= band.min) return band;
  return GAP;
}

/**
 * `other_*` fields complete a choice of "other" and are empty otherwise, so
 * their share says nothing about the data's quality.
 */
function isCompanion(field: string): boolean {
  return field.startsWith('other_');
}

/** fields filled at least once, most available first */
const bars = computed<Bar[]>(() =>
  (result.value?.buckets || [])
    .flatMap((bucket) => {
      const field = bucket.key[0];
      const a = bucket.availability;
      if (!field || !a?.total || !a.present || isCompanion(field)) return [];
      const share = a.present / a.total;
      const band = bandOf(share);
      return [
        {
          name: fieldLabel(field),
          value: share,
          present: a.present,
          total: a.total,
          itemStyle: { color: band.color },
          band: band.key,
        },
      ];
    })
    .sort((a, b) => b.value - a.value),
);

/** fields no record fills: listed under the chart, not drawn */
const neverFilled = computed(() =>
  (result.value?.buckets || []).flatMap((bucket) => {
    const field = bucket.key[0];
    return field && !bucket.availability?.present && !isCompanion(field)
      ? [fieldLabel(field)]
      : [];
  }),
);

const summary = computed(() => {
  const items = bars.value;
  if (!items.length) return '';
  const strong = items.filter((bar) => bar.band === 'strong').length;
  return `${t('plots.fields_count', items.length)} · ${t('plots.above_share', {
    count: strong,
    share: '80%',
  })}`;
});

const option = computed<EChartsOption>(() => {
  const items = bars.value;
  if (!items.length) return {};
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const bar = (Array.isArray(p) ? p[0] : p)?.data as Bar | undefined;
        if (!bar) return '';
        return [
          `<b>${bar.name}</b>`,
          `${t('plots.available')}: <b>${formatShare(bar.value)}</b>`,
          t('plots.present_of_total', {
            present: bar.present.toLocaleString(locale.value),
            total: bar.total.toLocaleString(locale.value),
          }),
          t(`plots.quality.${bar.band}`),
        ].join('<br/>');
      },
    },
    grid: { left: 8, right: 48, top: 8, bottom: 8, containLabel: true },
    xAxis: {
      type: 'value',
      min: 0,
      max: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: MUTED, formatter: (v: number) => formatShare(v) },
      splitLine: { lineStyle: { color: GRID, width: 1 } },
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: items.map((bar) => bar.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: TEXT, width: 170, overflow: 'truncate' },
    },
    series: [
      {
        type: 'bar',
        data: items,
        barCategoryGap: '30%',
        cursor: 'default',
        itemStyle: { borderRadius: [0, 4, 4, 0] },
        label: {
          show: true,
          position: 'right',
          color: TEXT,
          formatter: (p) => formatShare((p.data as Bar).value),
        },
      },
    ],
  };
});

/** Load the entity's fields: on mount, when the filters are applied, on a new entity. */
function reload(): void {
  void load({
    entity: entity.value,
    agg: 'availability',
    filter: exploreFilter(),
  });
}

function onEntity(value: ExploreEntity): void {
  entity.value = value;
  reload();
}

onMounted(reload);
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(reload);
});
</script>

<style scoped>
.band-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
</style>
