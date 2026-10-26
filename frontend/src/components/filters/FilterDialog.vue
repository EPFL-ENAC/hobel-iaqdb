<template>
  <q-dialog :model-value="modelValue" @update:model-value="(value) => emit('update:modelValue', value)" @before-show="open">
    <q-card class="filter-dialog">
      <nav class="filter-dialog__nav" :aria-label="t('filter_dialog.sections_label')">
        <button
          v-for="key in FILTER_SECTIONS"
          :key="key"
          type="button"
          class="filter-dialog__tab"
          :class="{ 'filter-dialog__tab--current': key === current }"
          :aria-current="key === current ? 'true' : undefined"
          @click="current = key"
        >
          <span class="filter-dialog__tab-title">
            {{ t(`filter_dialog.sections.${key}.title`) }}
            <span v-if="activeCount(draft, key)" class="filter-dialog__badge">{{ activeCount(draft, key) }}</span>
          </span>
          <span class="filter-dialog__tab-summary">{{ summaryOf(key) }}</span>
        </button>
        <q-space />
        <q-btn outline no-caps color="grey-8" class="filter-dialog__clear-all" :label="t('filter_dialog.clear_all')" @click="clearAll" />
      </nav>
      <section class="filter-dialog__main">
        <header class="filter-dialog__header">
          <h2 class="filter-dialog__title">{{ t(`filter_dialog.sections.${current}.title`) }}</h2>
          <q-btn v-close-popup flat round dense icon="close" :aria-label="t('ranked_bars.close')" />
        </header>
        <div class="filter-dialog__body">
          <component :is="SECTIONS[current]" :key="current" />
        </div>
        <footer class="filter-dialog__footer">
          <q-btn
            outline
            no-caps
            color="grey-8"
            :label="t('filter_dialog.clear_section', { section: t(`filter_dialog.sections.${current}.title`) })"
            @click="clearSection(draft, current)"
          />
          <q-btn
            unelevated
            no-caps
            color="grey-10"
            :loading="total.loading.value"
            :label="t('filter_dialog.show', total.count.value ?? 0)"
            @click="apply"
          />
        </footer>
      </section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/**
 * The explore filters in one dialog, a section at a time. It edits a draft
 * of the applied filters: the counts follow the draft as it changes, and
 * "Show N datasets" applies it at once; closing drops it.
 */
import BuildingsSection from '@/components/filters/BuildingsSection.vue';
import PeopleSection from '@/components/filters/PeopleSection.vue';
import SpacesSection from '@/components/filters/SpacesSection.vue';
import WhatWhenSection from '@/components/filters/WhatWhenSection.vue';
import WhereSection from '@/components/filters/WhereSection.vue';
import { exploreFilter } from '@/api/explore';
import {
  FILTER_DRAFT,
  FILTER_SECTIONS,
  activeCount,
  appliedDraft,
  applyDraft,
  clearSection,
  defaultDraft,
  type FilterSection,
} from '@/composables/useFilterDraft';
import { useExploreQuery } from '@/composables/useExploreQuery';
import { useFilterSummary } from '@/composables/useFilterSummary';

interface Props {
  modelValue: boolean;
  /** the section the dialog opens on */
  section?: FilterSection;
}

const props = withDefaults(defineProps<Props>(), { section: 'what' });
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>();
const { t } = useI18n();
const summary = useFilterSummary();

const SECTIONS: Record<FilterSection, Component> = {
  what: WhatWhenSection,
  where: WhereSection,
  buildings: BuildingsSection,
  spaces: SpacesSection,
  people: PeopleSection,
};

const draft = reactive(appliedDraft());
provide(FILTER_DRAFT, draft);
const current = ref<FilterSection>(props.section);

/** Start from the applied filters, on the section asked for. */
function open(): void {
  Object.assign(draft, appliedDraft());
  current.value = props.section;
}

/** the datasets the draft leaves, with a selected pollutant when there are some */
const totalQuery = useExploreQuery('metadata', () =>
  props.modelValue
    ? {
        entity: 'datasets',
        by: ['study'],
        filter: exploreFilter(draft),
        ...(draft.parameters.length ? { parameters: [...draft.parameters] } : {}),
      }
    : null,
);
const total = {
  count: computed(() => totalQuery.result.value?.meta.n ?? null),
  loading: totalQuery.loading,
};

function summaryOf(section: FilterSection): string {
  const values = summary.values(draft, section);
  return values.length ? values.join(' · ') : t(`filter_dialog.sections.${section}.subtitle`);
}

function clearAll(): void {
  Object.assign(draft, defaultDraft());
}

function apply(): void {
  applyDraft(draft);
  emit('update:modelValue', false);
}
</script>

<style scoped lang="scss">
.filter-dialog {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  width: 1180px;
  max-width: 96vw;
  height: 560px;
  max-height: 92vh;
  border-radius: 4px;
  overflow: hidden;

  @media (max-width: $breakpoint-sm-max) {
    grid-template-columns: minmax(0, 1fr);
    height: auto;
  }
}

.filter-dialog__nav {
  display: flex;
  flex-direction: column;
  background: $grey-3;

  @media (max-width: $breakpoint-sm-max) {
    flex-direction: row;
    overflow-x: auto;
  }
}

.filter-dialog__tab {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 12px;
  border: 0;
  background: none;
  font: inherit;
  text-align: left;
  cursor: pointer;

  &:hover {
    background: $grey-2;
  }
}

.filter-dialog__tab--current {
  background: white;

  &:hover {
    background: white;
  }
}

.filter-dialog__tab-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.875rem;
  color: $grey-10;
}

.filter-dialog__badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: $grey-10;
  font-size: 0.6875rem;
  line-height: 18px;
  text-align: center;
  color: white;
}

.filter-dialog__tab-summary {
  font-size: 0.8125rem;
  line-height: 1.4;
  color: $grey-7;
  // two lines at most, however many values
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;

  @media (max-width: $breakpoint-sm-max) {
    display: none;
  }
}

.filter-dialog__clear-all {
  margin: 12px;

  @media (max-width: $breakpoint-sm-max) {
    display: none;
  }
}

.filter-dialog__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.filter-dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 8px 32px;
}

.filter-dialog__title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 400;
  line-height: 1.3;
  color: $grey-10;
}

.filter-dialog__body {
  flex: 1;
  min-height: 0;
  padding: 16px 32px 24px;
  overflow-y: auto;
}

.filter-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 32px;
  border-top: 1px solid $grey-4;
}
</style>
