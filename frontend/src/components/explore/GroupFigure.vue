<template>
  <ChartCard :eyebrow="eyebrowText" :title="title" :footer-blank="!hasMore && !hint">
    <template #actions>
      <FigureMenu
        v-if="parameterOptions.length > 1"
        :label="t('explore_figures.groups.pollutant')"
        :model-value="parameter"
        :options="parameterOptions"
        @update:model-value="onParameter"
      />
      <!-- a line of its own: a short level name must not move it up beside the menu -->
      <div class="group-figure__path">
        <DrillPath :steps="steps" @pop="popTo" />
      </div>
    </template>
    <FigureFrame :height="0" fit="content" :loading="loading" :error="error" :empty="emptyMessage">
      <RangeList
        :rows="visible"
        :min="scale.min"
        :max="scale.max"
        :reference="reference"
        :min-rows="limit"
        @select="onSelect"
      />
    </FigureFrame>
    <ReferenceSource v-if="!emptyMessage" :parameter="parameter" :benchmark="benchmark" @pick="onReference" />
    <template #footer>
      <button v-if="hasMore" type="button" class="figure-link" @click="showAll = true">
        {{ t('ranked_bars.show_all', { count: rows.length }) }}
      </button>
      <span v-if="hint" class="group-figure__hint" :title="hint">
        <q-icon name="ads_click" size="16px" class="q-mr-xs" />{{ hint }}
      </span>
    </template>
    <FigureDialog v-model="showAll" :eyebrow="eyebrowText" :title="title" :loading="loading">
      <div class="group-figure__dialog-path">
        <DrillPath :steps="steps" @pop="popTo" />
      </div>
      <RangeList :rows="rows" :min="scale.min" :max="scale.max" :reference="reference" @select="onSelect" />
      <template v-if="hint" #footer>{{ hint }}</template>
    </FigureDialog>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * A pollutant's levels per group of one dimension (ventilation type,
 * climate, building type): the middle half of the means over the reference's
 * averaging period (hours, days, or one mean per space for a long-term
 * reference; days without a reference), the median as a dot and a number,
 * and the reference line. A
 * click on a group shows the groups of the next level of the path (a climate
 * group, its zones), then its datasets; a click on a dataset opens its study.
 */
import ChartCard from '@/components/explore/ChartCard.vue';
import DrillPath, { type DrillStep } from '@/components/explore/DrillPath.vue';
import FigureDialog from '@/components/explore/FigureDialog.vue';
import FigureFrame from '@/components/explore/FigureFrame.vue';
import FigureMenu from '@/components/explore/FigureMenu.vue';
import ReferenceSource from '@/components/explore/ReferenceSource.vue';
import RangeList, { type RangeRow } from '@/components/explore/RangeList.vue';
import { isUnknownKey, keyLabel, niceTicks, refine } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useParameterChoice } from '@/composables/useContextScope';
import { useDrillStack } from '@/composables/useDrillStack';
import { useExploreRequest } from '@/composables/useExploreQuery';
import { useFigureReference } from '@/composables/useFigureReference';
import type { ExploreBenchmark, ExploreParams, ExploreResult } from '@/models';

interface Props {
  /** what the pollutant is crossed with, e.g. "ventilation" */
  aspect: string;
  title: string;
  /** dimension keys from /stats/schema, one row per value: the first level, then each drill */
  path: string[];
  /** groups shown before the rest go to the "Show all" dialog */
  limit?: number;
}

/** The groups of one dimension of the path, or the datasets of one group. */
interface Level {
  /** the dimension of the groups, null for the datasets */
  by: string | null;
  stats: ExploreParams;
  /**
   * the measured datasets per group, for the labels: the same rows as the
   * levels, so a group's count is what its drill lists; none at the datasets level
   */
  counts: ExploreParams | null;
  datasets: boolean;
}

interface Loaded {
  stats: ExploreResult;
  counts: ExploreResult | null;
}

const props = withDefaults(defineProps<Props>(), { limit: 5 });
const i18n = useI18n();
const { t } = i18n;
const { formatValue } = useChartFormat();
const router = useRouter();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

/** the pollutants measured in at least one known group, under the filters; null until known */
const groupedRequest = useExploreRequest('measurements');
const grouped = computed(() => {
  const buckets = groupedRequest.result.value?.buckets;
  if (!buckets) return null;
  return new Set(buckets.flatMap((b) => (b.key[0] && !isUnknownKey(b.key[0]) && b.key[1] ? [b.key[1]] : [])));
});

// the pollutant is one of the page's selection with a known group: the default, else the first
const parameters = useParameterChoice({ among: grouped });
const { parameter, parameterOptions, parameterLabel, noDataMessage } = parameters;
const showAll = ref(false);

const statsRequest = useExploreRequest('measurements');
const countsRequest = useExploreRequest('measurements');
const shown = shallowRef<{ level: Level; loaded: Loaded } | null>(null);

/** the dimension of the first level, the one the pollutant must be known in */
const first = computed(() => props.path[0] ?? '');

const { stack, current, show, popTo } = useDrillStack<Level, Loaded>({
  fetch: async (level) => {
    const [stats, counts] = await Promise.all([
      statsRequest.load(level?.stats ?? null),
      countsRequest.load(level?.counts ?? null),
    ]);
    return stats ? { stats, counts } : null;
  },
  paint: (level, loaded) => {
    shown.value = { level, loaded };
    // the datasets are keyed by id: their names come from the catalog
    if (level.datasets)
      void exploreStore.loadDatasetNames(loaded.stats.buckets.flatMap((b) => (b.key[1] ? [b.key[1]] : [])));
  },
  clear: () => (shown.value = null),
});

const loading = computed(() => statsRequest.loading.value || countsRequest.loading.value);
/** the figure stands on the levels; the counts only add to it */
const error = computed(() => statsRequest.error.value);
const emptyMessage = computed(() =>
  !parameter.value || statsRequest.empty.value || (shown.value && !rows.value.length) ? noDataMessage.value : '',
);

const eyebrowText = computed(() =>
  t('explore_figures.groups.eyebrow', {
    pollutant: parameter.value ? parameterLabel.value : t('explore_figures.groups.pollutant'),
    aspect: props.aspect,
  }),
);

const { benchmark, pick } = useFigureReference(parameter);
const reference = computed(() => benchmark.value?.value ?? null);
/** the levels are means over the reference's averaging period, so the line and the boxes agree */
const grain = computed(() => benchmark.value?.grain ?? 'day');

/** the levels of the path, then the datasets: named in the header, the one shown marked */
const steps = computed<DrillStep[]>(() => {
  const groups = props.path.map((by) => {
    const levelKey = `explore_figures.level_names.${by}`;
    return i18n.te(levelKey) ? t(levelKey, 2) : (exploreStore.dimension(by)?.label ?? by).toLowerCase();
  });
  const names = [...groups, t('explore_figures.level_names.dataset', 2)];
  return names.map((name, i) => ({
    label: name.charAt(0).toUpperCase() + name.slice(1),
    state: i < stack.value.length - 1 ? 'past' : i === stack.value.length - 1 ? 'current' : 'next',
  }));
});

const hint = computed(() => {
  if (!shown.value || !rows.value.length) return '';
  return shown.value.level.datasets ? t('explore_figures.hint_open') : t('explore_figures.hint_drill');
});

/** Settle the pollutant, then restart from the groups: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  await groupedRequest.load(
    exploreStore.dimension(first.value)
      ? {
          agg: 'count',
          by: [first.value, 'parameter'],
          grain: 'day',
          filter: exploreFilter(),
          ...exploreRange(),
          ...(exploreStore.parameters.length ? { parameters: [...exploreStore.parameters] } : {}),
        }
      : null,
  );
  await parameters.refresh();
  await restart();
}

function onParameter(value: string | null): void {
  parameter.value = value;
  void restart();
}

/**
 * Another reference: the same drill at its averaging period. A reference
 * with the same period only moves the line, without a request.
 */
function onReference(b: ExploreBenchmark): void {
  const before = grain.value;
  pick(b);
  if (grain.value === before || !stack.value.length) return;
  void show(stack.value.map((level) => ({ ...level, stats: { ...level.stats, grain: grain.value } })));
}

onMounted(() => void refresh());
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refresh());
});

function restart(): Promise<void> {
  const slug = parameter.value;
  if (!slug || !exploreStore.dimension(first.value)) return show([]);
  return show([
    {
      by: first.value,
      stats: {
        agg: 'stats',
        by: [first.value],
        parameters: [slug],
        grain: grain.value,
        filter: exploreFilter(),
        ...exploreRange(),
      },
      // the datasets are the same at every grain: the daily rows are the lightest to count
      counts: {
        agg: 'count',
        by: [first.value, 'dataset'],
        parameters: [slug],
        grain: 'day',
        filter: exploreFilter(),
        ...exploreRange(),
      },
      datasets: false,
    },
  ]);
}

/**
 * A group shows the groups of the next level of the path in it, after the
 * last level its datasets, each with its study; a dataset opens its study.
 */
function onSelect(row: RangeRow): void {
  const level = current.value;
  if (!level) return;
  if (level.datasets || !level.by || !level.counts) {
    const study = row.key.split('/')[0];
    if (study) void router.push({ path: '/study', query: { id: study } });
    return;
  }
  const dimension = exploreStore.dimension(level.by);
  if (!dimension) return;
  const stats = refine(level.stats, dimension, row.key);
  const next = props.path[props.path.indexOf(level.by) + 1];
  if (next && exploreStore.dimension(next)) {
    const counts = refine(level.counts, dimension, row.key);
    void show([
      ...stack.value,
      { by: next, stats: { ...stats, by: [next] }, counts: { ...counts, by: [next, 'dataset'] }, datasets: false },
    ]);
    return;
  }
  stats.by = ['study', 'dataset'];
  void show([...stack.value, { by: null, stats, counts: null, datasets: true }]);
}

const unit = computed(() => shown.value?.loaded.stats.meta.unit || '');
/** what a bucket counts: hours, days or spaces, from the grain of the levels shown */
const periods = computed(() => t(`explore_figures.distribution.periods.${shown.value?.level.stats.grain ?? 'day'}`));

function withUnit(value: number): string {
  return unit.value ? `${formatValue(value)} ${unit.value}` : formatValue(value);
}

/** one row per known group, or per dataset, highest median first */
const rows = computed<RangeRow[]>(() => {
  const value = shown.value;
  if (!value) return [];
  const { level, loaded } = value;
  // a bucket per group and dataset: the group's count is its number of buckets
  const counts = new Map<string | null, number>();
  for (const b of loaded.counts?.buckets || []) {
    if (!b.key[1]) continue;
    const group = b.key[0] ?? null;
    counts.set(group, (counts.get(group) ?? 0) + 1);
  }
  return loaded.stats.buckets
    .flatMap((bucket) => {
      const stats = bucket.stats;
      if (!stats) return [];
      let key: string;
      let label: string;
      let sublabel: string;
      let clickable = true;
      if (level.datasets) {
        const [study, dataset] = bucket.key;
        // measurements tied to no dataset have nothing to list or open
        if (!dataset) return [];
        key = `${study ?? ''}/${dataset}`;
        label = keyLabel('dataset', dataset);
        sublabel = study ? keyLabel('study', study) : '';
        clickable = !!study;
      } else {
        const group = bucket.key[0];
        // an unknown group is no kind of ventilation, climate or building
        if (!group || isUnknownKey(group)) return [];
        const count = counts.get(group);
        key = group;
        label = keyLabel(level.by ?? first.value, group);
        sublabel = count === undefined ? '' : t('datasets_with_count', count);
      }
      return [
        {
          key,
          label,
          sublabel,
          value: formatValue(stats.p50),
          low: stats.p25,
          mid: stats.p50,
          high: stats.p75,
          clickable,
          tooltip: [
            t('explore_figures.distribution.tip_median', { value: withUnit(stats.p50) }),
            t('explore_figures.distribution.tip_middle', { low: withUnit(stats.p25), high: withUnit(stats.p75) }),
            t('explore_figures.distribution.tip_count', { count: bucket.n.toLocaleString(), periods: periods.value }),
          ],
        },
      ];
    })
    .sort((a, b) => b.mid - a.mid);
});

const hasMore = computed(() => rows.value.length > props.limit);
const visible = computed(() => rows.value.slice(0, props.limit));

/** one scale for the card and the dialog: every range and the reference in view */
const scale = computed(() => {
  const values = rows.value.flatMap((row) => [row.low, row.high]);
  if (reference.value !== null) values.push(reference.value);
  if (!values.length) return { min: 0, max: 1 };
  const ticks = niceTicks(Math.min(...values), Math.max(...values), 5);
  return { min: ticks[0] ?? 0, max: ticks[ticks.length - 1] ?? 1 };
});
</script>

<style scoped lang="scss">
.group-figure__path {
  flex-basis: 100%;
}

.group-figure__hint {
  min-width: 0;
  margin-left: auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: $grey-9;
}

.group-figure__dialog-path {
  margin-bottom: 16px;
  font-size: 0.6875rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: $grey-7;
}
</style>
