<template>
  <ChartCard :eyebrow="eyebrowText" :title="title" :note="note" :footer-blank="!hasMore && !legend">
    <template #actions>
      <FigureMenu
        v-if="parameterOptions.length > 1"
        :label="t('explore_figures.distribution.pollutant')"
        :model-value="parameter"
        :options="parameterOptions"
        @update:model-value="onParameter"
      />
      <FigureMenu
        :label="t('explore_figures.distribution.context')"
        :model-value="context"
        :options="contextOptions"
        @update:model-value="onContext"
      />
    </template>
    <FigureFrame :height="0" fit="content" :loading="loading" :error="error" :empty="emptyMessage">
      <DistributionTable
        :rows="visible"
        :ticks="ticks"
        :reference="benchmark?.value ?? null"
        :median="databaseMedian"
        :reference-text="referenceLine"
        :median-text="medianLine"
        :share-header="shareHeader"
        :axis-title="axisName"
        :min-rows="limit"
        :format-tick="formatValue"
        :format-share="formatShare"
      />
    </FigureFrame>
    <ReferenceSource
      v-if="!emptyMessage"
      :parameter="parameter"
      :benchmark="benchmark"
      compared
      @pick="onReference"
    />
    <template #footer>
      <button v-if="hasMore" type="button" class="figure-link" @click="showAll = true">
        {{ t('ranked_bars.show_all', { count: rows.length }) }}
      </button>
      <span v-if="legend" class="distribution-figure__legend">{{ legend }}</span>
    </template>
    <FigureDialog v-model="showAll" :eyebrow="eyebrowText" :title="title" :note="note" :width="1000">
      <DistributionTable
        :rows="rows"
        :ticks="ticks"
        :reference="benchmark?.value ?? null"
        :median="databaseMedian"
        :reference-text="referenceLine"
        :median-text="medianLine"
        :share-header="shareHeader"
        :axis-title="axisName"
        :format-tick="formatValue"
        :format-share="formatShare"
      />
      <template v-if="legend" #footer>{{ legend }}</template>
    </FigureDialog>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * How a pollutant's levels spread in each group of a context, against the
 * pollutant's reference and the median of the whole database, with each
 * group's share of periods at or below the reference. The levels are means
 * over the reference's averaging period: hourly, daily, or one per space for
 * a long-term reference.
 */
import ChartCard from '@/components/explore/ChartCard.vue';
import DistributionTable, { type DistributionRow } from '@/components/explore/DistributionTable.vue';
import FigureDialog from '@/components/explore/FigureDialog.vue';
import FigureFrame from '@/components/explore/FigureFrame.vue';
import FigureMenu from '@/components/explore/FigureMenu.vue';
import ReferenceSource from '@/components/explore/ReferenceSource.vue';
import { keyLabel, niceTicks, withUnitName } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useChartFormat } from '@/composables/useChartFormat';
import { useContextChoice, useParameterChoice } from '@/composables/useContextScope';
import { useExploreRequest } from '@/composables/useExploreQuery';
import { useFigureReference } from '@/composables/useFigureReference';
import type { ExploreBenchmark, ExploreParams } from '@/models';

interface Props {
  eyebrow: string;
  title: string;
  /** groups shown before the rest go to the "Show all" dialog */
  limit?: number;
}

const props = withDefaults(defineProps<Props>(), { limit: 6 });
const i18n = useI18n();
const { t } = i18n;
const { formatValue, formatShare, describeReference, withPollutants } = useChartFormat();
const filtersStore = useFiltersStore();

const parameters = useParameterChoice({ withBenchmark: true });
const { parameter, parameterOptions, noDataMessage } = parameters;
const contexts = useContextChoice(parameter);
const { context, contextOptions, contextDimension } = contexts;
/** the pollutant shown, said in the eyebrow: the menu is there only when there is a choice */
const eyebrowText = computed(() => withPollutants(props.eyebrow, parameter.value ? [parameter.value] : []));
const showAll = ref(false);

/** the levels per group, under the filters */
const statsRequest = useExploreRequest('measurements');
/** the share of periods above the reference per group, under the filters */
const exceedanceRequest = useExploreRequest('measurements');
/** the median of the whole database, filters aside */
const databaseRequest = useExploreRequest('measurements');
/** the datasets per group, for the labels */
const datasetsRequest = useExploreRequest('metadata');

const { benchmark, pick } = useFigureReference(parameter);

const loading = computed(
  () =>
    statsRequest.loading.value ||
    exceedanceRequest.loading.value ||
    databaseRequest.loading.value ||
    datasetsRequest.loading.value,
);
/** the figure stands on the levels; the other requests only add to it */
const error = computed(() => statsRequest.error.value);

const emptyMessage = computed(() => {
  if (!parameter.value || !benchmark.value) return noDataMessage.value;
  return statsRequest.empty.value ? noDataMessage.value : '';
});

/** Settle the menus, then load: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  await parameters.refresh();
  await contexts.refresh();
  await reload();
}

async function onParameter(value: string | null): Promise<void> {
  parameter.value = value;
  await contexts.refresh();
  await reload();
}

function onContext(value: string | null): void {
  context.value = value;
  void reload();
}

onMounted(() => void refresh());
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refresh());
});

/** another reference: other levels and shares when its averaging differs */
function onReference(b: ExploreBenchmark): void {
  pick(b);
  void reload();
}

/** The four requests of the context and pollutant; none when either is missing. */
async function reload(): Promise<void> {
  const dimension = contextDimension.value;
  const b = benchmark.value;
  const slug = parameter.value;
  const ready = !!dimension && !!slug && !!b;
  // the reference's averaging period sets the grain of the levels and the shares
  const base: ExploreParams | null = ready ? { by: [dimension.key], parameters: [slug], grain: b.grain } : null;
  const scoped = { filter: exploreFilter(), ...exploreRange() };
  await Promise.all([
    statsRequest.load(base && { ...base, ...scoped, agg: 'stats' }),
    exceedanceRequest.load(base && { ...base, ...scoped, agg: 'exceedance', threshold: b?.value ?? 0 }),
    databaseRequest.load(ready ? { by: ['parameter'], parameters: [slug], grain: b.grain, agg: 'stats' } : null),
    datasetsRequest.load(
      ready ? { entity: 'datasets', by: [dimension.key], parameters: [slug], ...scoped } : null,
    ),
  ]);
}

const databaseMedian = computed(() => databaseRequest.result.value?.buckets[0]?.stats?.p50 ?? null);

const unit = computed(() => statsRequest.result.value?.meta.unit || benchmark.value?.unit || '');

function withUnit(value: number): string {
  return unit.value ? `${formatValue(value)} ${unit.value}` : formatValue(value);
}

/** one row per group with levels, highest median first */
const rows = computed<DistributionRow[]>(() => {
  const dimension = contextDimension.value;
  if (!dimension) return [];
  const shares = new Map(
    (exceedanceRequest.result.value?.buckets || []).map((b) => [b.key[0] ?? null, b.exceedance?.share]),
  );
  const datasets = new Map((datasetsRequest.result.value?.buckets || []).map((b) => [b.key[0] ?? null, b.n]));
  const periods = t(`explore_figures.distribution.periods.${benchmark.value?.grain ?? 'day'}`);
  return (statsRequest.result.value?.buckets || [])
    .flatMap((bucket, i) => {
      const key = bucket.key[0] ?? null;
      const stats = bucket.stats;
      if (!stats) return [];
      const above = shares.get(key);
      const count = datasets.get(key);
      return [
        {
          // keys are unique, null aside
          key: key ?? `null-${i}`,
          label: key === null ? t('plots.unknown') : keyLabel(dimension.key, key),
          sublabel: count === undefined ? '' : t('datasets_with_count', count),
          stats,
          share: above === undefined ? null : 1 - above,
          tooltip: [
            t('explore_figures.distribution.tip_median', { value: withUnit(stats.p50) }),
            t('explore_figures.distribution.tip_middle', { low: withUnit(stats.p25), high: withUnit(stats.p75) }),
            t('explore_figures.distribution.tip_range', { low: withUnit(stats.p05), high: withUnit(stats.p95) }),
            t('explore_figures.distribution.tip_count', { count: bucket.n.toLocaleString(), periods }),
          ],
        },
      ];
    })
    .sort((a, b) => b.stats.p50 - a.stats.p50);
});

const hasMore = computed(() => rows.value.length > props.limit);
const visible = computed(() => rows.value.slice(0, props.limit));

/** one scale for the card and the dialog: every group, the reference and the median in view */
const ticks = computed(() => {
  const values = rows.value.flatMap((row) => [row.stats.p05, row.stats.p95]);
  if (benchmark.value) values.push(benchmark.value.value);
  if (databaseMedian.value !== null) values.push(databaseMedian.value);
  if (!values.length) return [0, 1];
  return niceTicks(Math.min(...values), Math.max(...values), 6);
});

const referenceText = computed(() => (benchmark.value ? describeReference(benchmark.value) : ''));

const shareHeader = computed(() =>
  benchmark.value
    ? t('explore_figures.distribution.share_header', {
        periods: t(`explore_figures.distribution.periods.${benchmark.value.grain}`),
        value: referenceText.value,
      })
    : '',
);

/** written beside the two lines */
const referenceLine = computed(() =>
  benchmark.value ? t('explore_figures.distribution.line_reference', { value: withUnit(benchmark.value.value) }) : '',
);
const medianLine = computed(() =>
  databaseMedian.value === null
    ? ''
    : t('explore_figures.distribution.line_median', { value: withUnit(databaseMedian.value) }),
);

/** what the lines stand for, under the figure; the note says what the boxes are */
const legend = computed(() => {
  if (!benchmark.value || !rows.value.length) return '';
  return [
    t('explore_figures.distribution.legend_reference', { value: referenceText.value }),
    ...(databaseMedian.value === null
      ? []
      : [t('explore_figures.distribution.legend_median', { value: withUnit(databaseMedian.value) })]),
  ].join(' · ');
});

/** the grain of the levels, the reference's averaging period */
const grain = computed(() => benchmark.value?.grain ?? 'day');

/** the scale's title, under the ticks */
const axisName = computed(() => withUnitName(t(`explore_figures.mean_axis.${grain.value}`), unit.value));

/** "building type": the context's level name, its label when not translated */
const contextName = computed(() => {
  const dimension = contextDimension.value;
  if (!dimension) return '';
  const key = `explore_figures.level_names.${dimension.key}`;
  return i18n.te(key) ? t(key, 1) : dimension.label.toLowerCase();
});

/** what one row is, then that a gap between the groups has more causes than the context */
const note = computed(() => {
  if (!contextName.value || !benchmark.value) return '';
  return [
    t('explore_figures.distribution.reading', {
      level: contextName.value,
      means: t(`explore_figures.means_of.${grain.value}`),
    }),
    t('explore_figures.caveat', { level: contextName.value }),
  ].join(' ');
});
</script>

<style scoped lang="scss">
.distribution-figure__legend {
  min-width: 0;
  margin-left: auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: $grey-8;
}
</style>
