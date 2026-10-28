<template>
  <ChartCard :eyebrow="eyebrow" :title="title" :footer-blank="!hasMore">
    <template #panel>
      <div class="availability-figure__label">{{ t('explore_figures.metadata_availability.score_fields_of') }}</div>
      <q-btn-toggle
        v-model="entity"
        class="availability-figure__toggle"
        :options="entityOptions"
        no-caps
        unelevated
        spread
        color="white"
        text-color="grey-10"
        toggle-color="grey-10"
        toggle-text-color="white"
      />
      <!-- kept in place on every pick, shown on one: the panel keeps its height -->
      <div class="availability-figure__note" :class="{ invisible: entity !== 'datasets' }">
        {{ t('explore_figures.metadata_availability.datasets_note') }}
      </div>
      <ul class="availability-figure__legend">
        <li v-for="band in BANDS" :key="band.key">
          <span class="availability-figure__swatch" :style="`background: ${band.color};`" />
          <span class="availability-figure__band">{{ t(`explore_figures.metadata_availability.bands.${band.key}`) }}</span>
          <span class="text-grey-7">{{ t(`explore_figures.metadata_availability.bands.${band.key}_range`) }}</span>
        </li>
      </ul>
    </template>
    <!-- always there, empty or not: the panel keeps its height -->
    <template #footer>
      <button v-if="hasMore" type="button" class="figure-link" @click="showAll = true">
        {{ t('ranked_bars.show_all', { count: rows.length }) }}
      </button>
    </template>
    <RankedBars
      v-model:show-all="showAll"
      :rows="rows"
      :limit="limit"
      :summary="summary"
      combine="mean"
      :footer="false"
      :label-header="t('explore_figures.metadata_availability.field_availability')"
      :value-header="t('explore_figures.metadata_availability.reliability')"
      :format-value="formatShare"
      :dialog-eyebrow="eyebrow"
      :dialog-title="title"
      :loading="loading"
    >
      <template v-if="error" #message>
        <span class="text-negative text-caption">{{ t('plots.error') }}: {{ error }}</span>
      </template>
      <template v-else-if="empty" #message>
        <span class="text-grey-7 text-caption">{{ t('plots.no_data') }}</span>
      </template>
    </RankedBars>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * The share of records where each descriptive field is filled in, for the
 * entity picked, banded by how far it can be relied on, with their average
 * on top.
 */
import ChartCard from '@/components/explore/ChartCard.vue';
import RankedBars from '@/components/explore/RankedBars.vue';
import type { RankedRow, RankedSummary } from '@/components/explore/ranked';
import { FIGURE_ACCENT, FIGURE_CHECK, FIGURE_GAP } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type { ExploreBucket, ExploreEntity } from '@/models';

type ScoredEntity = 'studies' | 'buildings' | 'spaces' | 'datasets';

interface Props {
  eyebrow: string;
  title: string;
  /** fields shown before the rest are averaged into "Other" */
  limit?: number;
}

const props = withDefaults(defineProps<Props>(), { limit: 15 });
const i18n = useI18n();
const { t } = i18n;
const { formatCount, formatShare } = useChartFormat();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

/** how far a field can be relied on, by its share filled in, best first */
const BANDS = [
  { key: 'reliable', min: 0.8, color: FIGURE_ACCENT },
  { key: 'check', min: 0.7, color: FIGURE_CHECK },
  { key: 'gap', min: 0, color: FIGURE_GAP },
] as const;
/**
 * What is scored for each pick: a dataset's own columns are load
 * bookkeeping, its description is in the variables of its files.
 */
const SCORED: Record<ScoredEntity, ExploreEntity> = {
  studies: 'studies',
  buildings: 'buildings',
  spaces: 'spaces',
  datasets: 'variables',
};
/** where each entity's field labels live in the i18n messages */
const LABELS: Record<ScoredEntity, string> = {
  studies: 'study',
  buildings: 'study.building',
  spaces: 'study.space',
  datasets: 'explore_figures.metadata_availability.variable_fields',
};
/** fields whose message key has another name than the column */
const LABEL_ALIASES: Partial<Record<ScoredEntity, Record<string, string>>> = {
  studies: { website: 'url' },
  buildings: { long: 'longitude', lat: 'latitude' },
};

const entity = ref<ScoredEntity>('buildings');
const showAll = ref(false);

const entityOptions = computed(() =>
  (['studies', 'buildings', 'spaces', 'datasets'] as const).map((value) => ({
    value,
    label: t(`explore_figures.entities.${value}`),
  })),
);

const { result, loading, error, load } = useExploreRequest('metadata');

/** Load the fields of the entity picked: on mount, on a pick, and when the filters are applied. */
function reload(): void {
  const parameters = exploreStore.parameters.length ? { parameters: [...exploreStore.parameters] } : {};
  void load({ entity: SCORED[entity.value], agg: 'availability', filter: exploreFilter(), ...exploreRange(), ...parameters });
}

onMounted(reload);
watch(entity, reload);
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(reload);
});

/**
 * No entity matches the filters. `meta.n` counts filled values here, so a
 * match whose fields are all empty still lists them as never filled.
 */
const empty = computed(
  () => result.value !== null && !result.value.buckets.some((bucket) => bucket.availability?.total),
);

function fieldLabel(field: string): string {
  const key = LABEL_ALIASES[entity.value]?.[field] ?? field;
  const path = `${LABELS[entity.value]}.${key}`;
  if (i18n.te(path)) return t(path);
  const words = field.replace(/_/g, ' ');
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** the best band a share reaches, on the rounded percent the label shows */
function colorOf(share: number): string {
  const shown = Math.round(share * 100) / 100;
  // the last band starts at 0: every share reaches one
  return (BANDS.find((band) => shown >= band.min) ?? BANDS[2]).color;
}

/**
 * `other_*` fields complete a choice of "other" and are empty otherwise, so
 * their share says nothing about the data's quality.
 */
function isCompanion(field: string): boolean {
  return field.startsWith('other_');
}

/** every field, never filled ones included, most available first */
const rows = computed<RankedRow<ExploreBucket>[]>(() =>
  (result.value?.buckets || [])
    .flatMap((bucket) => {
      const field = bucket.key[0];
      const a = bucket.availability;
      if (!field || !a?.total || isCompanion(field)) return [];
      const share = a.present / a.total;
      return [
        {
          key: field,
          label: fieldLabel(field),
          value: share,
          color: colorOf(share),
          title: t('explore_figures.metadata_availability.filled', {
            present: formatCount(a.present),
            total: formatCount(a.total),
          }),
          data: bucket,
        },
      ];
    })
    .sort((a, b) => b.value - a.value),
);

/** more fields than the list shows: they are averaged into "Other" */
const hasMore = computed(() => rows.value.length > props.limit + 1);

/** the fields' mean share: how much of a description is there, on average; blank until loaded */
const summary = computed<RankedSummary>(() => {
  const items = rows.value;
  return {
    label: t('explore_figures.metadata_availability.all'),
    value: items.length ? items.reduce((sum, row) => sum + row.value, 0) / items.length : null,
    color: FIGURE_CHECK,
    ...(items.length ? { title: t('explore_figures.metadata_availability.all_hint', items.length) } : {}),
  };
});
</script>

<style scoped lang="scss">
.availability-figure__label {
  margin-bottom: 12px;
  font-size: 0.9375rem;
  color: $grey-10;
}

.availability-figure__toggle {
  border: 1px solid $grey-10;
  border-radius: 0;
  max-width: 360px;

  :deep(.q-btn) {
    border-radius: 0;
  }

  :deep(.q-btn + .q-btn) {
    border-left: 1px solid $grey-10;
  }
}

.availability-figure__note {
  margin-top: 12px;
  font-size: 0.8125rem;
  color: $grey-7;
}

.availability-figure__legend {
  margin: 32px 0 0;
  padding: 24px 0 0;
  border-top: 1px solid $grey-4;
  list-style: none;
  font-size: 0.9375rem;

  li {
    display: flex;
    align-items: center;
    gap: 8px;
    // the global `li + li` margin is for prose lists
    margin: 0 0 8px;
  }
}

.availability-figure__swatch {
  width: 14px;
  height: 14px;
}

.availability-figure__band {
  color: $grey-10;
}
</style>
