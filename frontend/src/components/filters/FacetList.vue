<template>
  <div class="facet-list">
    <q-btn-toggle
      v-if="sortable"
      v-model="order"
      :options="orders"
      dense
      flat
      no-caps
      size="sm"
      toggle-color="teal-8"
      class="facet-list__order"
      :aria-label="t('filter_dialog.sort_label')"
    />
    <q-input
      v-if="searchable"
      v-model="search"
      dense
      outlined
      clearable
      :placeholder="searchPlaceholder"
      class="facet-list__search"
    >
      <template #prepend><q-icon name="search" size="18px" /></template>
    </q-input>
    <label
      v-for="option in shown"
      :key="option.value"
      class="facet-list__row"
      :class="{ 'facet-list__row--disabled': option.disabled }"
      :title="option.title || option.label"
    >
      <q-checkbox
        :aria-label="option.label"
        :model-value="modelValue.includes(option.value)"
        :disable="option.disabled"
        dense
        size="sm"
        color="teal-6"
        @update:model-value="(on: boolean) => toggle(option.value, on)"
      />
      <span class="facet-list__label">{{ option.label }}</span>
      <span class="facet-list__track"><span class="facet-list__bar" :style="`width: ${widthOf(option.count)}%;`" /></span>
      <span class="facet-list__count">{{ option.count.toLocaleString() }}</span>
    </label>
    <button v-if="hidden > 0" type="button" class="figure-link facet-list__more" @click="expanded = true">
      {{ t('filter_dialog.show_more', { count: hidden }) }}
    </button>
  </div>
</template>

<script setup lang="ts">
/**
 * Values to pick several of: a checkbox, the label, a bar and the count
 * each; the first `limit` shown, the rest on demand, a search above when
 * there are many. With `sortable`, the reader orders them by count or A to Z.
 * With `searchKeys`, the search matches the key of a value too.
 */
import type { FacetOption } from '@/components/filters/facets';

interface Props {
  modelValue: string[];
  /** most counted first */
  options: FacetOption[];
  limit?: number;
  searchable?: boolean;
  searchPlaceholder?: string;
  /** opt-in: country keys are ISO codes, so "de" would find Germany */
  searchKeys?: boolean;
  sortable?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  limit: 7,
  searchable: false,
  searchPlaceholder: '',
  searchKeys: false,
  sortable: false,
});
const emit = defineEmits<{ 'update:modelValue': [value: string[]] }>();
const { t } = useI18n();

const search = ref<string | null>('');
const expanded = ref(false);
const order = ref<'count' | 'label'>('count');
const orders = computed(() => [
  { value: 'count', label: t('filter_dialog.sort_count') },
  { value: 'label', label: t('filter_dialog.sort_label_az') },
]);

// A to Z keeps the options that only say ("Not reported") last
const ordered = computed(() =>
  order.value === 'count'
    ? props.options
    : [...props.options].sort(
        (a, b) => Number(!!a.disabled) - Number(!!b.disabled) || a.label.localeCompare(b.label),
      ),
);
// the label, or with `searchKeys` the key too: "co2" finds "CO₂"
const matching = computed(() => {
  const needle = (search.value || '').trim().toLowerCase();
  const matches = (o: FacetOption) =>
    o.label.toLowerCase().includes(needle) || (props.searchKeys && o.value.toLowerCase().includes(needle));
  return needle ? ordered.value.filter(matches) : ordered.value;
});
// a search, or a value picked past the limit, shows every match
const shown = computed(() =>
  expanded.value || search.value ? matching.value : matching.value.slice(0, props.limit),
);
const hidden = computed(() => matching.value.length - shown.value.length);
const max = computed(() => Math.max(1, ...props.options.map((o) => o.count)));

function widthOf(count: number): number {
  return (count / max.value) * 100;
}

function toggle(value: string, on: boolean): void {
  const next = props.modelValue.filter((v) => v !== value);
  emit('update:modelValue', on ? [...next, value] : next);
}
</script>

<style scoped lang="scss">
.facet-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.875rem;
  color: $grey-10;
}

.facet-list__order {
  align-self: flex-start;
  margin-bottom: 8px;
}

.facet-list__search {
  margin-bottom: 12px;
}

.facet-list__row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) 72px 32px;
  align-items: center;
  gap: 10px;
  min-height: 28px;
  cursor: pointer;
}

.facet-list__row--disabled {
  cursor: default;
  color: $grey-7;
}

.facet-list__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.facet-list__track {
  height: 4px;
  background: $figure-muted;
}

.facet-list__bar {
  display: block;
  height: 100%;
  background: $figure-accent;
}

.facet-list__count {
  font-size: 0.75rem;
  color: $grey-7;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.facet-list__more {
  align-self: flex-start;
  margin-top: 8px;
}
</style>
