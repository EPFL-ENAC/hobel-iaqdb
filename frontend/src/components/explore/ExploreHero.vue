<template>
  <section class="explore-hero explore-section">
    <div class="explore-container">
      <div class="explore-hero__eyebrow">{{ t('explore_hero.eyebrow') }}</div>
      <h1 class="explore-hero__title">{{ title }}</h1>
      <p class="explore-hero__lead">{{ t('explore_hero.lead') }}</p>
      <div v-if="error" class="text-negative text-caption q-mb-sm">
        {{ t('explore_hero.error') }}: {{ error }}
      </div>
      <div class="explore-hero__stats">
        <dl class="explore-hero__grid">
          <div v-for="stat in stats" :key="stat.key" class="explore-hero__stat">
            <dt class="explore-hero__label">{{ stat.label }}</dt>
            <dd class="explore-hero__value">
              <q-skeleton v-if="stat.value === null && loading" type="text" width="4ch" />
              <template v-else>{{ stat.value ?? '–' }}</template>
            </dd>
          </div>
        </dl>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { exploreFilter, exploreRange } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';

const { t, locale } = useI18n();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

// the same requests as the country and coverage charts: they share the cache
const datasetsRequest = useExploreRequest('metadata');
const countriesRequest = useExploreRequest('metadata');
const coverageRequest = useExploreRequest('measurements');

/** Load the numbers: on mount and when the filters are applied. */
function reload(): void {
  const filter = exploreFilter();
  const range = exploreRange();
  const parameters = exploreStore.parameters.length ? { parameters: [...exploreStore.parameters] } : {};
  // one study per dataset: the study buckets add up to the distinct datasets
  void datasetsRequest.load({ entity: 'datasets', by: ['study'], filter, ...range, ...parameters });
  void countriesRequest.load({ entity: 'datasets', by: ['country'], filter, ...range, ...parameters });
  // coverage holds lifetime totals and spans: within a year range, count
  // the measured days instead, by year for the span
  void coverageRequest.load({
    ...('from' in range || 'to' in range
      ? { agg: 'count', by: ['parameter', 'year'] }
      : { agg: 'coverage', by: ['parameter'] }),
    filter,
    ...range,
    ...parameters,
  });
}

onMounted(reload);
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(reload);
});

const loading = computed(
  () =>
    datasetsRequest.loading.value ||
    countriesRequest.loading.value ||
    coverageRequest.loading.value,
);
const error = computed(
  () =>
    datasetsRequest.error.value ||
    countriesRequest.error.value ||
    coverageRequest.error.value,
);

const datasets = computed(() => datasetsRequest.result.value?.meta.n ?? null);
const countries = computed(() => {
  const result = countriesRequest.result.value;
  return result ? result.buckets.filter((b) => b.key[0] !== null).length : null;
});
const records = computed(() => {
  const result = coverageRequest.result.value;
  return result ? (result.meta.n_records ?? 0) : null;
});
const parameters = computed(() => {
  const result = coverageRequest.result.value;
  return result ? new Set(result.buckets.map((b) => b.key[0])).size : null;
});

/** first and last year measured; naive timestamps, read as text */
const years = computed<[number, number] | null>(() => {
  let first: string | undefined;
  let last: string | undefined;
  for (const bucket of coverageRequest.result.value?.buckets || []) {
    // a coverage span, or a counted year
    const from = bucket.coverage?.first_at ?? bucket.key[1] ?? undefined;
    const to = bucket.coverage?.last_at ?? bucket.key[1] ?? undefined;
    if (from && (!first || from < first)) first = from;
    if (to && (!last || to > last)) last = to;
  }
  return first && last ? [Number(first.slice(0, 4)), Number(last.slice(0, 4))] : null;
});

function formatCount(value: number): string {
  return value.toLocaleString(locale.value);
}

/** 47.8M rather than 47,812,345 */
function formatRecords(value: number): string {
  return new Intl.NumberFormat(locale.value, {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}

/** "2010–24" within a century, "1999–2024" across, "2018" for one year */
function formatYears([first, last]: [number, number]): string {
  if (first === last) return `${first}`;
  const sameCentury = Math.floor(first / 100) === Math.floor(last / 100);
  const end = sameCentury ? String(last % 100).padStart(2, '0') : `${last}`;
  return `${first}–${end}`;
}

const title = computed(() => {
  if (datasets.value === null || countries.value === null) return t('explore_hero.title_loading');
  if (datasets.value === 0) return t('explore_hero.title_empty');
  return t('explore_hero.title', {
    datasets: t('explore_hero.datasets', datasets.value),
    countries: t('explore_hero.countries', countries.value),
  });
});

const stats = computed(() => [
  {
    key: 'datasets',
    value: datasets.value === null ? null : formatCount(datasets.value),
    label: t('explore_hero.stats.datasets', datasets.value ?? 2),
  },
  {
    key: 'countries',
    value: countries.value === null ? null : formatCount(countries.value),
    label: t('explore_hero.stats.countries', countries.value ?? 2),
  },
  {
    key: 'records',
    value: records.value === null ? null : formatRecords(records.value),
    label: t('explore_hero.stats.records', records.value ?? 2),
  },
  {
    key: 'parameters',
    value: parameters.value === null ? null : formatCount(parameters.value),
    label: t('explore_hero.stats.parameters', parameters.value ?? 2),
  },
  {
    key: 'years',
    value: years.value === null ? null : formatYears(years.value),
    label: t('explore_hero.stats.years'),
  },
]);
</script>

<style scoped lang="scss">
.explore-hero {
  background: white;
}

.explore-hero__eyebrow {
  font-size: 0.8125rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: $grey-10;
  margin-bottom: 12px;
}

.explore-hero__title {
  font-size: clamp(1.75rem, 1.2rem + 1.8vw, 2.75rem);
  font-weight: 400;
  line-height: 1.2;
  letter-spacing: -0.01em;
  color: $grey-10;
  max-width: 22ch;
  margin: 0 0 24px;
}

.explore-hero__lead {
  font-size: clamp(1rem, 0.9rem + 0.4vw, 1.25rem);
  line-height: 1.6;
  color: $grey-10;
  max-width: 42ch;
  margin: 0 0 40px;
}

.explore-hero__stats {
  border-top: 1px solid $grey-10;
  border-bottom: 1px solid $grey-4;
  // clips the left divider of the first column
  overflow: hidden;
}

.explore-hero__grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  margin: 0 0 0 -1px;

  @media (max-width: $breakpoint-sm-max) {
    grid-template-columns: repeat(3, 1fr);
  }

  @media (max-width: $breakpoint-xs-max) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.explore-hero__stat {
  display: flex;
  // the term follows its value on screen
  flex-direction: column-reverse;
  justify-content: flex-end;
  padding: 14px 20px;
  border-left: 1px solid $grey-4;

  // rows after the first are divided from the one above
  @media (max-width: $breakpoint-sm-max) {
    box-shadow: 0 -1px 0 $grey-4;
  }
}

.explore-hero__value {
  margin: 0;
  font-size: clamp(1.375rem, 1.2rem + 0.5vw, 1.75rem);
  line-height: 1.3;
  color: $grey-10;
  font-variant-numeric: tabular-nums;
}

.explore-hero__label {
  font-size: 0.875rem;
  color: $grey-7;
}
</style>
