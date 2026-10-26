<template>
  <div class="filter-section" style="--columns: 3">
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.countries') }}</div>
      <FacetList
        v-model="draft.countries"
        :options="countryOptions"
        searchable
        :search-placeholder="t('filter_dialog.search_countries', { count: countryOptions.length })"
      />
    </div>
    <div>
      <div class="filter-section__group">
        <div class="filter-section__heading">
          {{ draft.countries.length ? t('filter_dialog.cities_in_countries') : t('filter_dialog.cities') }}
        </div>
        <FacetChips v-model="draft.cities" :options="cityOptions" :limit="7" />
      </div>
      <div class="filter-section__group">
        <div class="filter-section__heading">{{ t('filter_dialog.climate_zone') }}</div>
        <FacetChips v-model="draft.climate_zones" :options="climateChips" :empty-label="climateEmpty" />
      </div>
    </div>
    <div>
      <div class="filter-section__heading">{{ t('filter_dialog.altitude') }}</div>
      <RangeHistogram
        v-model="draft.altitudes"
        :min="DEFAULT_ALTITUDES.min"
        :max="DEFAULT_ALTITUDES.max"
        :step="100"
        :bins="altitudeBins"
        :width="250"
        :caption="isAnyAltitude ? t('filter_dialog.any_altitude') : ''"
        :format="(v: number) => `${v} m`"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/** Where the buildings stand: countries, cities, climate zones, altitude. */
import FacetChips from '@/components/filters/FacetChips.vue';
import FacetList from '@/components/filters/FacetList.vue';
import RangeHistogram from '@/components/filters/RangeHistogram.vue';
import { notReported, toOptions, type FacetOption } from '@/components/filters/facets';
import { keyLabel } from '@/components/plots/charts';
import { FILTER_DRAFT } from '@/composables/useFilterDraft';
import { useFacetCounts } from '@/composables/useFacetCounts';
import { DEFAULT_ALTITUDES } from '@/stores/filters';
import { climateOptions } from '@/utils/options';

const { t } = useI18n();
const draft = inject(FILTER_DRAFT)!;

const countries = useFacetCounts(draft, { by: ['country'], own: ['countries', 'cities'] });
const cities = useFacetCounts(draft, { by: ['city', 'country'], own: ['cities'] });
const climates = useFacetCounts(draft, { by: ['climate_zone'], own: ['climate_zones'] });
const altitudes = useFacetCounts(draft, { by: ['altitude_band'], own: ['altitudes'] });

// a city outside the countries picked would leave nothing: it is dropped with its country
watch(
  () => [...draft.countries],
  (countries) => {
    if (!countries.length) return;
    const kept = draft.cities.filter((city) => countries.includes(city.slice(-2)));
    // only a change is written: an equal list would still wake every count
    if (kept.length !== draft.cities.length) draft.cities = kept;
  },
);

const countryOptions = computed(() => toOptions(countries.counts.value, (key) => keyLabel('country', key)));

/** keyed "City|CC", picked as the store keeps them: "City, CC" */
const cityOptions = computed<FacetOption[]>(() =>
  toOptions(cities.counts.value, (key) => key.split('|')[0] ?? key).map((option) => ({
    ...option,
    value: option.value.replace('|', ', '),
  })),
);

/** "Cfb · Temperate", the full description on hover */
const climateChips = computed<FacetOption[]>(() => {
  const options = toOptions(climates.counts.value, (code) => {
    const label = keyLabel('climate_zone', code).replace(/^\[\w+\]\s*/, '');
    return `${code} · ${label.split(',')[0]}`;
  }).map((option) => ({ ...option, title: keyLabel('climate_zone', option.value) }));
  const unknown = notReported(climates.counts.value, t('filter_dialog.not_reported'));
  return unknown ? [...options, unknown] : options;
});

const climateEmpty = computed(() => {
  const withData = new Set(climates.counts.value.keys());
  const none = climateOptions.filter((opt) => !withData.has(opt.value)).length;
  return none ? t('filter_dialog.zones_no_data', none) : '';
});

const altitudeBins = computed(
  () => new Map([...altitudes.counts.value].flatMap(([key, n]) => (key === null ? [] : [[Number(key), n] as const]))),
);

const isAnyAltitude = computed(
  () => draft.altitudes.min === DEFAULT_ALTITUDES.min && draft.altitudes.max === DEFAULT_ALTITUDES.max,
);
</script>
