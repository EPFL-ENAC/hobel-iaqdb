<template>
  <button
    v-if="benchmarks.length > 1"
    type="button"
    class="reference-menu"
    :title="t('explore_figures.reference_menu.change')"
  >
    <span class="reference-menu__mark" aria-hidden="true" />
    <span class="reference-menu__value">{{ selectedLabel }}</span>
    <q-icon name="arrow_drop_down" size="16px" class="reference-menu__arrow" />
    <q-menu anchor="bottom left" self="top left" @before-show="reset">
      <div class="reference-menu__panel">
        <q-input
          v-model="search"
          dense
          outlined
          autofocus
          clearable
          :placeholder="t('explore_figures.reference_menu.search')"
          class="reference-menu__search"
        >
          <template #prepend>
            <q-icon name="search" />
          </template>
        </q-input>
        <q-list dense class="reference-menu__list">
          <!-- first step: the regions; a click shows the references of one -->
          <template v-if="!region && !words.length">
            <q-item
              v-for="group in regions"
              :key="group.region"
              clickable
              :active="group.region === selected?.region"
              active-class="reference-menu__item--active"
              @click="region = group.region"
            >
              <q-item-section>
                <q-item-label>{{ group.region }}</q-item-label>
                <q-item-label caption>{{ t('explore_figures.reference_menu.count', group.items.length) }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-icon name="chevron_right" />
              </q-item-section>
            </q-item>
          </template>
          <template v-else>
            <q-item
              v-if="region"
              clickable
              class="reference-menu__back"
              :aria-label="t('explore_figures.reference_menu.back')"
              @click="region = null"
            >
              <q-item-section avatar>
                <q-icon name="arrow_back" size="20px" />
              </q-item-section>
              <q-item-section>{{ region }}</q-item-section>
            </q-item>
            <template v-for="group in groups" :key="group.region">
              <q-item-label v-if="!region" header class="reference-menu__region">{{ group.region }}</q-item-label>
              <q-item
                v-for="b in group.items"
                :key="b.id"
                v-close-popup
                clickable
                :active="b.id === selected?.id"
                active-class="reference-menu__item--active"
                @click="emit('pick', b)"
              >
                <q-item-section>
                  <q-item-label lines="2">{{ describeReference(b) }} · {{ b.source }}</q-item-label>
                  <q-item-label caption lines="1">{{ caption(b) }}</q-item-label>
                </q-item-section>
                <q-item-section v-if="b.is_default" side top>
                  <span class="reference-menu__default">{{ t('explore_figures.reference_menu.default') }}</span>
                </q-item-section>
              </q-item>
            </template>
            <q-item v-if="!groups.length">
              <q-item-section class="text-grey-8">{{ t('explore_figures.reference_menu.no_match') }}</q-item-section>
            </q-item>
          </template>
        </q-list>
        <p class="reference-menu__note">{{ t('explore_figures.reference_menu.note') }}</p>
      </div>
    </q-menu>
  </button>
  <span v-else-if="selected" class="reference-menu reference-menu--single">
    <span class="reference-menu__mark" aria-hidden="true" />
    <span class="reference-menu__value">{{ selectedLabel }}</span>
  </span>
</template>

<script setup lang="ts">
/**
 * The reference a pollutant is compared with, as a small red pill. The red
 * mark stands for the red reference line of the charts. With one reference,
 * the pill shows it and does not open. With more, it opens a menu: first a
 * region, then a reference of that region. A search lists the matches of
 * every region, or of the open one. The figure holds the choice, so a pick
 * changes that figure only.
 */
import { useChartFormat } from '@/composables/useChartFormat';
import type { ExploreBenchmark } from '@/models';

const props = defineProps<{
  parameter: string | null;
  /** the reference of the figure, shown in the pill and marked in the menu */
  selected: ExploreBenchmark | null;
}>();
const emit = defineEmits<{ pick: [benchmark: ExploreBenchmark] }>();
const { t } = useI18n();
const { describeReference } = useChartFormat();
const exploreStore = useExploreStore();

const search = ref<string | null>('');
/** the region opened in the menu; null lists the regions */
const region = ref<string | null>(null);

/** each opening starts on the list of regions */
function reset(): void {
  search.value = '';
  region.value = null;
}

/** in the schema's order: the default first, then worldwide, then by region */
const benchmarks = computed(() => exploreStore.benchmarksOf(props.parameter));
/** the value only: the line around the pill names the source */
const selectedLabel = computed(() => (props.selected ? describeReference(props.selected) : ''));

function caption(b: ExploreBenchmark): string {
  const by = b.year === null ? b.institution : `${b.institution}, ${b.year}`;
  return [by, b.limit_type, b.period].join(' · ');
}

function searchText(b: ExploreBenchmark): string {
  return [describeReference(b), b.source, caption(b), b.region, b.setting ?? ''].join(' ').toLocaleLowerCase();
}

const words = computed(() => (search.value ?? '').toLocaleLowerCase().split(/\s+/).filter(Boolean));

/** the references by region, in the schema's order: the default's region first */
function byRegion(list: ExploreBenchmark[]): { region: string; items: ExploreBenchmark[] }[] {
  const out: { region: string; items: ExploreBenchmark[] }[] = [];
  for (const b of list) {
    let group = out.find((g) => g.region === b.region);
    if (!group) out.push((group = { region: b.region, items: [] }));
    group.items.push(b);
  }
  return out;
}

const regions = computed(() => byRegion(benchmarks.value));

/** the references of the open region, or of every region, that match every word of the search */
const groups = computed(() =>
  byRegion(
    benchmarks.value.filter((b) => {
      if (region.value && b.region !== region.value) return false;
      const text = searchText(b);
      return words.value.every((word) => text.includes(word));
    }),
  ),
);
</script>

<style scoped lang="scss">
// a pill, unlike the square menus of the card header, tinted like the reference line
.reference-menu {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 100%;
  min-width: 0;
  height: 20px;
  padding: 0 2px 0 7px;
  border: 1px solid rgba($figure-gap, 0.45);
  border-radius: 10px;
  background: rgba($figure-gap, 0.06);
  font: inherit;
  font-size: 0.75rem;
  font-weight: 500;
  color: $grey-10;
  white-space: nowrap;
  cursor: pointer;

  &:hover {
    border-color: $figure-gap;
    background: rgba($figure-gap, 0.1);
  }

  &:focus-visible {
    outline: 2px solid $figure-gap;
    outline-offset: 1px;
  }
}

.reference-menu--single {
  padding-right: 7px;
  cursor: default;

  &:hover {
    border-color: rgba($figure-gap, 0.45);
    background: rgba($figure-gap, 0.06);
  }
}

// the reference line of the charts, in small
.reference-menu__mark {
  flex: none;
  width: 12px;
  height: 2px;
  background: $figure-gap;
}

.reference-menu__value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-menu__arrow {
  flex: none;
  color: $grey-8;
}

.reference-menu__panel {
  width: min(480px, calc(100vw - 32px));
}

.reference-menu__search {
  margin: 12px 12px 4px;
}

.reference-menu__list {
  max-height: 360px;
  overflow-y: auto;
}

.reference-menu__back {
  font-weight: 500;
  border-bottom: 1px solid $grey-4;
}

.reference-menu__region {
  padding-top: 12px;
  padding-bottom: 4px;
  font-size: 0.75rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: $grey-7;
}

.reference-menu__item--active {
  color: $figure-accent-strong;
  background: rgba(74, 163, 154, 0.08);
}

.reference-menu__default {
  font-size: 0.6875rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: $grey-7;
}

.reference-menu__note {
  margin: 0;
  padding: 8px 16px 12px;
  border-top: 1px solid $grey-4;
  font-size: 0.75rem;
  color: $grey-8;
}
</style>
