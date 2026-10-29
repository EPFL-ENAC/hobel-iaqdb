<template>
  <ChartCard :eyebrow="eyebrow" :title="title">
    <RankedBars
      :rows="rows"
      :limit="limit"
      :label-header="shown ? levelName(shown.level.dimension, 2) : ''"
      :value-header="t(`explore_figures.entities.${entity}`)"
      :highlighted="highlighted"
      :layout="layout"
      :dialog-eyebrow="eyebrow"
      :dialog-title="title"
      :loading="loading"
      @select="(row) => select(row.data, row.label)"
    >
      <template v-if="error" #message>
        <span class="text-negative text-caption">{{ t('plots.error') }}: {{ error }}</span>
      </template>
      <template v-else-if="empty" #message>
        <span class="text-grey-7 text-caption">
          {{ parameterLabels ? t('plots.no_data_for', { parameters: parameterLabels }) : t('plots.no_data') }}
          <span v-if="availableLabels">{{ t('plots.available_parameters', { parameters: availableLabels }) }}</span>
        </span>
      </template>
      <template v-if="chain.length > 1 && shown" #label-header>
        <DrillPath :steps="steps" @pop="popTo" />
      </template>
      <template v-if="hint" #hint>
        <q-icon name="ads_click" size="16px" class="q-mr-xs" />{{ hint }}
      </template>
    </RankedBars>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * Entities counted per category, ranked; a click on a row goes down the
 * path one level, the table header tells where the drill stands.
 */
import ChartCard from '@/components/explore/ChartCard.vue';
import DrillPath, { type DrillStep } from '@/components/explore/DrillPath.vue';
import RankedBars from '@/components/explore/RankedBars.vue';
import type { RankedRow } from '@/components/explore/ranked';
import { isUnknownKey } from '@/components/plots/charts';
import { useMetadataDrill } from '@/composables/useMetadataDrill';
import type { ExploreBucket, ExploreDimension, ExploreEntity } from '@/models';

interface Props {
  eyebrow: string;
  title: string;
  /** catalog entity counted per key */
  entity: ExploreEntity;
  /**
   * Dimension keys from /stats/schema, the levels a click goes down through:
   * the chart opens on the first, a click on the last opens its catalog view
   */
  path: string[];
  /** `drill` (default): a click goes down one level; `filter`: it sets the global filter; `none`: read-only */
  click?: 'drill' | 'filter' | 'none';
  /** count only entities that contain the selected parameters */
  withParameters?: boolean;
  /** rows shown before the rest are summed into "Other" */
  limit?: number;
  /** how a row is laid out: `stacked` for narrow figures */
  layout?: 'inline' | 'stacked';
}

const props = withDefaults(defineProps<Props>(), {
  click: 'drill',
  withParameters: true,
  limit: 10,
  layout: 'inline',
});
const i18n = useI18n();
const { t } = i18n;
const exploreStore = useExploreStore();

const {
  result,
  loading,
  error,
  empty,
  stack,
  shown,
  chain,
  clickable,
  selectedKeys,
  popTo,
  label,
  select,
} = useMetadataDrill(props);

/** "country" (1) or "countries" (2), the dimension label when not translated */
function levelName(dimension: ExploreDimension, count: number): string {
  const key = `explore_figures.level_names.${dimension.key}`;
  return i18n.te(key) ? t(key, count) : dimension.label.toLowerCase();
}

function capitalized(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** the drill path: the levels gone through, the one shown, those below */
const steps = computed<DrillStep[]>(() =>
  chain.value.map((dimension, i) => ({
    label: capitalized(levelName(dimension, 2)),
    state: i < stack.value.length - 1 ? 'past' : i === stack.value.length - 1 ? 'current' : 'next',
  })),
);

/**
 * One row per known key, in the order received; missing and 'unknown' keys
 * summed into a last "Unknown" row, not clickable: no filter matches both.
 */
const rows = computed<RankedRow<ExploreBucket>[]>(() => {
  const value = shown.value;
  if (!value) return [];
  const dimension = value.level.dimension;
  const known = value.result.buckets.filter((bucket) => !isUnknownKey(bucket.key[0]));
  const unknown = value.result.buckets.filter((bucket) => isUnknownKey(bucket.key[0]));
  const out: RankedRow<ExploreBucket>[] = known.map((bucket) => ({
    key: bucket.key[0] as string,
    label: label(dimension, bucket.key[0]),
    value: bucket.n,
    clickable: clickable.value,
    data: bucket,
  }));
  if (unknown.length) {
    const n = unknown.reduce((sum, bucket) => sum + bucket.n, 0);
    out.push({
      key: 'unknown',
      label: label(dimension, null),
      value: n,
      clickable: false,
      data: { key: [null], n },
    });
  }
  return out;
});

/** in `filter` mode, the keys in the global filters; else every row */
const highlighted = computed(() =>
  selectedKeys.value.size ? [...selectedKeys.value] : undefined,
);

/** what a click on a row does, said under the chart; the header says which level is next */
const hint = computed(() => {
  const level = shown.value?.level;
  if (!level || !clickable.value) return '';
  if (props.click === 'filter') return t('explore_figures.hint_filter');
  // the level shown, not the one loading: the stack moves first
  return stack.value.indexOf(level) + 1 < props.path.length
    ? t('explore_figures.hint_drill')
    : t('explore_figures.hint_open');
});

const parameterLabels = computed(() =>
  props.withParameters
    ? exploreStore.parameters.map(exploreStore.parameterLabel).join(', ')
    : '',
);

const availableLabels = computed(() =>
  (result.value?.meta.available_parameters || [])
    .map(exploreStore.parameterLabel)
    .join(', '),
);
</script>
