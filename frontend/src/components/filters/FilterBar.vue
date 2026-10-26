<template>
  <div class="filter-bar">
    <div class="filter-bar__inner">
      <div class="filter-bar__sentence">
        <span>{{ t('filter_bar.showing') }}</span>
        <button type="button" class="filter-bar__pill" :class="{ 'filter-bar__pill--set': applied.parameters.length }" @click="openOn('what')">
          {{ summary.pollutants(applied) }}
        </button>
        <span>{{ t('filter_bar.measured') }}</span>
        <button type="button" class="filter-bar__pill" :class="{ 'filter-bar__pill--set': yearsSet }" @click="openOn('what')">
          {{ summary.years(applied) }}
        </button>
        <template v-for="section in PLACE_SECTIONS" :key="section">
          <span class="filter-bar__dot" aria-hidden="true">·</span>
          <button
            type="button"
            class="filter-bar__pill"
            :class="{ 'filter-bar__pill--set': activeCount(applied, section) }"
            :title="summary.values(applied, section).join(', ') || undefined"
            @click="openOn(section)"
          >
            {{ summary.pill(applied, section) }}
          </button>
        </template>
        <button v-if="changed" type="button" class="filter-bar__reset" @click="reset">{{ t('filter_bar.reset') }}</button>
      </div>
      <div class="filter-bar__totals">
        <div class="filter-bar__count">{{ datasetsText }}</div>
        <div class="filter-bar__records">{{ recordsText }}</div>
      </div>
      <q-btn
        unelevated
        no-caps
        color="grey-10"
        icon="download"
        class="filter-bar__download"
        :label="t('explore_download.button')"
        @click="showDownload = true"
      />
    </div>
    <FilterDialog v-model="showDialog" :section="section" />
    <DownloadDialog v-model="showDownload" />
  </div>
</template>

<script setup lang="ts">
/**
 * The applied filters as a sentence ("showing CO₂ measured 2010–2024 ·
 * anywhere · any building…"), each part opening its section of the filter
 * dialog, with what the filters leave and the download.
 */
import DownloadDialog from '@/components/DownloadDialog.vue';
import FilterDialog from '@/components/filters/FilterDialog.vue';
import { exploreFilter, exploreRange } from '@/api/explore';
import { shortParameterName } from '@/components/plots/charts';
import { useChartFormat } from '@/composables/useChartFormat';
import { useExploreRequest } from '@/composables/useExploreQuery';
import {
  FILTER_SECTIONS,
  activeCount,
  appliedDraft,
  defaultDraft,
  type FilterSection,
} from '@/composables/useFilterDraft';
import { useFilterSummary } from '@/composables/useFilterSummary';

const { t } = useI18n();
const { formatCompact } = useChartFormat();
const summary = useFilterSummary();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

/** the sections after the pollutants and years, each a pill */
const PLACE_SECTIONS = FILTER_SECTIONS.filter((s) => s !== 'what');

const showDialog = ref(false);
const showDownload = ref(false);
const section = ref<FilterSection>('what');

/** the applied filters, read again when they are applied */
const applied = computed(() => {
  void filtersStore.updates;
  void exploreStore.parameters;
  return appliedDraft();
});

const yearsSet = computed(() => summary.years(applied.value) !== t('filter_bar.any_year'));

/** anything off its default: the reset link shows */
const changed = computed(() => {
  const defaults = defaultDraft();
  return FILTER_SECTIONS.some((s) => activeCount(applied.value, s) > 0) ||
    applied.value.parameters.join() !== defaults.parameters.join();
});

function openOn(target: FilterSection): void {
  section.value = target;
  showDialog.value = true;
}

function reset(): void {
  filtersStore.reset();
  exploreStore.resetParameters();
  filtersStore.notifyUpdate();
}

const datasetsRequest = useExploreRequest('metadata');
// the same request as the coverage figure: they share the cache
const recordsRequest = useExploreRequest('measurements');

/** Load the totals: on mount and when the filters are applied. */
function reload(): void {
  const parameters = exploreStore.parameters.length ? { parameters: [...exploreStore.parameters] } : {};
  void datasetsRequest.load({ entity: 'datasets', by: ['study'], filter: exploreFilter(), ...parameters });
  void recordsRequest.load({ agg: 'coverage', by: ['parameter'], filter: exploreFilter(), ...exploreRange() });
}

onMounted(() => {
  void exploreStore.loadSchema();
  reload();
});
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(reload);
});

const datasetsText = computed(() => {
  const n = datasetsRequest.result.value?.meta.n;
  return n === undefined ? '' : t('datasets_with_count', n);
});

/** "11.1M CO₂ records", or every pollutant's when none is selected */
const recordsText = computed(() => {
  const buckets = recordsRequest.result.value?.buckets;
  if (!buckets) return '';
  const selected = new Set(exploreStore.parameters);
  const records = buckets.reduce(
    (sum, b) => (b.key[0] && (!selected.size || selected.has(b.key[0])) ? sum + (b.n_records ?? 0) : sum),
    0,
  );
  const which = exploreStore.parameters.length === 1 ? shortParameterName(exploreStore.parameters[0] ?? '') : '';
  return t('filter_bar.records', { count: formatCompact(records), pollutant: which }).replace(/\s+/g, ' ');
});
</script>

<style scoped lang="scss">
.filter-bar {
  border-top: 1px solid $grey-4;
  background: white;
  color: $grey-10;
}

.filter-bar__inner {
  display: flex;
  align-items: center;
  gap: 12px 24px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 10px 24px;

  @media (max-width: $breakpoint-xs-max) {
    flex-wrap: wrap;
    padding: 10px 16px;
  }
}

.filter-bar__sentence {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 8px;
  flex: 1;
  min-width: 0;
  font-size: 1rem;
}

.filter-bar__pill {
  max-width: 220px;
  padding: 3px 14px;
  border: 1px solid $grey-10;
  border-radius: 999px;
  background: white;
  font: inherit;
  font-size: 0.875rem;
  color: $grey-10;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;

  &:hover {
    background: $grey-2;
  }

  &:focus-visible {
    outline: 2px solid $figure-accent;
    outline-offset: 2px;
  }
}

.filter-bar__pill--set {
  background: $grey-10;
  color: white;

  &:hover {
    background: $grey-9;
  }
}

.filter-bar__dot {
  color: $grey-8;
}

.filter-bar__reset {
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  font-size: 0.875rem;
  color: $grey-10;
  text-decoration: underline;
  text-underline-offset: 0.2em;
  cursor: pointer;
}

.filter-bar__totals {
  text-align: right;
  white-space: nowrap;

  @media (max-width: $breakpoint-xs-max) {
    text-align: left;
  }
}

.filter-bar__count {
  font-size: 0.875rem;
}

.filter-bar__records {
  font-size: 0.8125rem;
  color: $grey-7;
}

.filter-bar__download {
  border-radius: 2px;
}
</style>
