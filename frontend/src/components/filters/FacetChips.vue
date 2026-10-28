<template>
  <div class="facet-chips">
    <button
      v-for="option in shown"
      :key="option.value || option.label"
      type="button"
      class="facet-chips__chip"
      :class="{
        'facet-chips__chip--on': isOn(option.value),
        'facet-chips__chip--disabled': option.disabled,
      }"
      :disabled="option.disabled"
      :title="option.title || option.label"
      :aria-pressed="option.disabled ? undefined : isOn(option.value)"
      @click="toggle(option.value)"
    >
      <span class="facet-chips__label">{{ option.label }}</span>
      <span class="facet-chips__count">{{ option.count.toLocaleString() }}</span>
    </button>
    <button v-if="hidden > 0" type="button" class="facet-chips__chip facet-chips__chip--more" @click="expanded = true">
      {{ t('filter_dialog.more', { count: hidden }) }}
    </button>
    <span v-if="emptyLabel" class="facet-chips__chip facet-chips__chip--empty">{{ emptyLabel }}</span>
  </div>
</template>

<script setup lang="ts">
/**
 * Values as chips, each with its count: a click picks or drops it. With
 * `single`, picking one drops the others. Disabled chips only say, e.g.
 * "Not reported"; `emptyLabel` sums up the values with no data.
 */
import type { FacetOption } from '@/components/filters/facets';

interface Props {
  /** the values picked: a list, or one value or none with `single` */
  modelValue: string[] | string | null;
  options: FacetOption[];
  single?: boolean;
  /** chips shown before "+ N more"; all by default */
  limit?: number;
  /** a dashed chip after the others, e.g. "28 zones with no data" */
  emptyLabel?: string;
}

const props = withDefaults(defineProps<Props>(), { single: false, limit: Infinity, emptyLabel: '' });
const emit = defineEmits<{ 'update:modelValue': [value: string[] | string | null] }>();
const { t } = useI18n();

const expanded = ref(false);

const picked = computed(() =>
  Array.isArray(props.modelValue) ? props.modelValue : props.modelValue ? [props.modelValue] : [],
);
// the picked chips stay in view, whatever the limit
const shown = computed(() =>
  expanded.value
    ? props.options
    : props.options.filter((o, i) => i < props.limit || picked.value.includes(o.value)),
);
const hidden = computed(() => props.options.length - shown.value.length);

function isOn(value: string): boolean {
  return picked.value.includes(value);
}

function toggle(value: string): void {
  if (props.single) {
    emit('update:modelValue', isOn(value) ? null : value);
    return;
  }
  const rest = picked.value.filter((v) => v !== value);
  emit('update:modelValue', isOn(value) ? rest : [...rest, value]);
}
</script>

<style scoped lang="scss">
.facet-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.facet-chips__chip {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  max-width: 100%;
  padding: 5px 10px;
  border: 1px solid $grey-4;
  border-radius: 2px;
  background: white;
  font: inherit;
  font-size: 0.875rem;
  color: $grey-10;
  cursor: pointer;

  &:hover:not(:disabled) {
    border-color: $grey-7;
  }
}

.facet-chips__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.facet-chips__count {
  font-size: 0.75rem;
  color: $grey-7;
}

.facet-chips__chip--on {
  border-color: $grey-10;
  background: $grey-10;
  color: white;

  .facet-chips__count {
    color: $grey-4;
  }
}

.facet-chips__chip--disabled {
  cursor: default;
  color: $grey-8;
}

.facet-chips__chip--more {
  color: $figure-accent-strong;
}

.facet-chips__chip--empty {
  border-style: dashed;
  color: $grey-6;
  cursor: default;
}
</style>
