<template>
  <div class="filter-bar">
    <div class="filter-bar__inner">
      <div class="filter-bar__sentence">
        <button type="button" class="filter-bar__icon" @click="openOn('what')">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 6.5h17M6.5 12h11M9.5 17.5h5" /></svg>
          {{ t('filter_bar.label') }}
        </button>
        <span>{{ t('filter_bar.showing') }}</span>
        <button type="button" class="filter-bar__pill" :class="{ 'filter-bar__pill--set': applied.parameters.length }" :aria-label="pillLabel(summary.pollutants(applied))" @click="openOn('what')">
          <span class="filter-bar__pill-text">{{ summary.pollutants(applied) }}</span>
          <svg class="filter-bar__chevron" viewBox="0 0 12 12" aria-hidden="true"><path d="M3 4.5 6 7.5 9 4.5" /></svg>
        </button>
        <span>{{ t('filter_bar.measured') }}</span>
        <button type="button" class="filter-bar__pill" :class="{ 'filter-bar__pill--set': yearsSet }" :aria-label="pillLabel(summary.years(applied))" @click="openOn('what')">
          <span class="filter-bar__pill-text">{{ summary.years(applied) }}</span>
          <svg class="filter-bar__chevron" viewBox="0 0 12 12" aria-hidden="true"><path d="M3 4.5 6 7.5 9 4.5" /></svg>
        </button>
        <template v-for="section in PLACE_SECTIONS" :key="section">
          <span class="filter-bar__dot" aria-hidden="true">·</span>
          <button
            type="button"
            class="filter-bar__pill"
            :class="{ 'filter-bar__pill--set': activeCount(applied, section) }"
            :title="summary.values(applied, section).join(', ') || undefined"
            :aria-label="pillLabel(summary.pill(applied, section))"
            @click="openOn(section)"
          >
            <span class="filter-bar__pill-text">{{ summary.pill(applied, section) }}</span>
            <svg class="filter-bar__chevron" viewBox="0 0 12 12" aria-hidden="true"><path d="M3 4.5 6 7.5 9 4.5" /></svg>
          </button>
        </template>
        <button v-if="changed" type="button" class="filter-bar__reset" @click="reset">{{ t('filter_bar.reset') }}</button>
      </div>
      <div class="filter-bar__actions">
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

/** what a screen reader says for a pill: its value, and that it opens the filters */
function pillLabel(value: string): string {
  return t('filter_bar.pill_label', { value });
}

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
  void datasetsRequest.load({ entity: 'datasets', by: ['study'], filter: exploreFilter(), ...exploreRange(), ...parameters });
  const range = exploreRange();
  // coverage holds lifetime totals: within a year range, count the measured days
  const agg = 'from' in range || 'to' in range ? 'count' : 'coverage';
  void recordsRequest.load({ agg, by: ['parameter'], filter: exploreFilter(), ...range });
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
  // the whole window width, not the 1400px column of the page: the sentence stays on one line
  padding: 10px 24px;

  @media (max-width: $breakpoint-sm-max) {
    flex-wrap: wrap;
    row-gap: 0;
    padding-bottom: 0;
  }

  @media (max-width: $breakpoint-xs-max) {
    padding: 10px 16px 0;
  }
}

// the totals and download: beside the sentence on a wide screen, a band of
// their own under it on a phone or tablet
.filter-bar__actions {
  display: contents;

  @media (max-width: $breakpoint-sm-max) {
    display: flex;
    align-items: center;
    gap: 16px;
    // the full width of the bar, through its padding
    flex: 0 0 calc(100% + 48px);
    margin: 12px -24px 0;
    padding: 8px 24px;
    border-top: 1px solid $grey-4;
    background: $grey-1;
  }

  @media (max-width: $breakpoint-xs-max) {
    flex-basis: calc(100% + 32px);
    margin: 12px -16px 0;
    padding: 8px 16px;
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

  // on a phone or tablet the sentence takes the whole row, the totals and download go below
  @media (max-width: $breakpoint-sm-max) {
    flex-basis: 100%;
    gap: 8px;
  }
}

// a "filter list" (three lines, each shorter) at the start of the sentence: says what the pills after it
// do, and opens the filters too
.filter-bar__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-right: 4px;
  padding: 2px;
  border: none;
  background: none;
  font: inherit;
  font-size: 0.875rem;
  font-weight: 500; // about as thick as the icon's lines
  color: $figure-accent; // the green of the charts
  cursor: pointer;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  transition: color 0.1s;

  svg {
    width: 22px;
    height: 22px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.75;
    stroke-linecap: round;
  }

  @media (hover: hover) {
    &:hover {
      color: $figure-accent-strong;
    }
  }

  &:focus-visible {
    outline: 2px solid $figure-accent-strong;
    outline-offset: 2px;
    border-radius: 4px;
  }
}

.filter-bar__pill {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  max-width: 220px;
  padding: 3px 8px 3px 14px;
  border: 1px solid $grey-10;
  border-radius: 999px;
  background: white;
  font: inherit;
  font-size: 0.875rem;
  color: $grey-10;
  white-space: nowrap;
  cursor: pointer;
  // no double-tap zoom delay, no grey flash: the active state gives the feedback
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  transition: background-color 0.1s, border-color 0.1s;

  // a touch screen keeps the hover after a tap: hover only where there is a mouse
  @media (hover: hover) {
    &:hover {
      border-color: $figure-accent-strong;
      background: $figure-accent-tint;
    }
  }

  &:active {
    background: #bfe0dc; // the accent tint, a step darker
  }

  &:focus-visible {
    outline: 2px solid $figure-accent;
    outline-offset: 2px;
  }

  // a finger needs a bigger target than a mouse, and the whole width for long values
  @media (max-width: $breakpoint-sm-max) {
    min-height: 40px;
    max-width: 100%;
    padding: 6px 10px 6px 16px;
    font-size: 0.9375rem;
  }
}

// the value is cut with an ellipsis, the chevron always shows
.filter-bar__pill-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

// a dropdown arrow: the pill opens a choice
.filter-bar__chevron {
  flex: none;
  width: 12px;
  height: 12px;
  margin-left: 4px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.25;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: transform 0.15s;

  @media (hover: hover) {
    .filter-bar__pill:hover & {
      transform: translateY(1px);
    }
  }
}

.filter-bar__pill--set {
  background: $grey-10;
  color: white;

  @media (hover: hover) {
    &:hover {
      border-color: $grey-10;
      background: $grey-9;
    }
  }

  &:active {
    background: $grey-8;
  }
}

.filter-bar__dot {
  color: $grey-8;

  // the dots end up alone at the end of wrapped lines: the gap separates the pills
  @media (max-width: $breakpoint-sm-max) {
    display: none;
  }
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
  touch-action: manipulation;

  @media (max-width: $breakpoint-sm-max) {
    min-height: 40px;
    padding: 0 8px;
    font-size: 0.9375rem;
  }
}

.filter-bar__totals {
  text-align: right;
  white-space: nowrap;

  @media (max-width: $breakpoint-sm-max) {
    flex: 1;
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

  @media (max-width: $breakpoint-sm-max) {
    min-height: 44px;
  }
}
</style>
